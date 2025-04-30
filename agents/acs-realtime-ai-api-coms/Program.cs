using Azure.Communication.CallAutomation;
using Azure.Communication;
using Azure.Messaging;
using Azure.Messaging.EventGrid;
using Azure.Messaging.EventGrid.SystemEvents;
using Microsoft.AspNetCore.Mvc;
using Microsoft.AspNetCore.Mvc.ModelBinding;
using Newtonsoft.Json;
using System.ComponentModel.DataAnnotations;
using CallAutomationOpenAI;
using Azure.Communication.Sms;
using Azure;
using acstalk.Models;

var builder = WebApplication.CreateBuilder(args);
builder.WebHost.UseUrls("http://localhost:8000");

// add swagger
builder.Services.AddEndpointsApiExplorer();
builder.Services.AddSwaggerGen();

//Get ACS Connection String from appsettings.json
var acsConnectionString = builder.Configuration.GetValue<string>("AcsConnectionString");
ArgumentNullException.ThrowIfNullOrEmpty(acsConnectionString);

//ACS Clients
CallAutomationClient client = new CallAutomationClient(acsConnectionString);
SmsClient SmsClient = new SmsClient(acsConnectionString);
builder.Services.AddSingleton(client);
builder.Services.AddSingleton(SmsClient);

var app = builder.Build();
app.UseSwagger();
app.UseSwaggerUI();
var appBaseUrl = builder.Configuration.GetValue<string>("DevTunnelUri")?.TrimEnd('/');

if (string.IsNullOrEmpty(appBaseUrl))
{
    var websiteHostName = Environment.GetEnvironmentVariable("WEBSITE_HOSTNAME");
    Console.WriteLine($"websiteHostName :{websiteHostName}");
    appBaseUrl = $"https://{websiteHostName}";
    Console.WriteLine($"appBaseUrl :{appBaseUrl}");
}


app.MapGet("/", () => "Hello ACS CallAutomation!");


app.MapPost("/api/sendSms", async (
    [FromBody] SendSmsRequest request,
    ILogger<Program> logger,
    IConfiguration configuration,
    SmsClient smsClient) =>
{
    string from = new PhoneNumberIdentifier(builder.Configuration.GetValue<string>("SmsAgentPhoneNumber")).ToString();

    // send sms to the target phone numbers
    try
    {
        Response<IReadOnlyList<SmsSendResult>> response = await smsClient.SendAsync(
            from: from,
            to: request.TargetPhoneNumbers,
            message: request.NewAlertData ?? "This is a test alert message from the government. Please ignore.",
            options: new SmsSendOptions(enableDeliveryReport: true)
            {
                Tag = "Alerts",
            }
        );

        IEnumerable<SmsSendResult> results = response.Value;
        foreach (SmsSendResult result in results)
        {
            Console.WriteLine($"Sms id: {result.MessageId}");
            Console.WriteLine($"Send Result Successful: {result.Successful}");
        }
    }
    catch (Exception ex)
    {
        Console.WriteLine($"Error sending SMS: {ex.Message}");
        return Results.Problem(ex.Message);
    }
    
    return Results.Ok("SMS sent successfully");
});


app.MapPost("/api/initiateOutboundCall", async (
    [FromBody] OutboundCallRequest request,
    ILogger<Program> logger,
    CallAutomationClient client,
    IConfiguration configuration) =>
{
    // Updating the system prompt with the request data for reference during conversation
    string requestBody = JsonConvert.SerializeObject(request, Formatting.Indented);
    AzureOpenAIService.UpdateSystemPromptTemplate(requestBody);

    // extract agent_phone_number from requestBody as string
    var acsPhoneNumber = configuration.GetValue<string>("AgentPhoneNumber");
    logger.LogInformation($"Agent Phone Number: {acsPhoneNumber}");
    logger.LogInformation($"appBaseUrl: {appBaseUrl}");
    logger.LogInformation($"Acs Connection String: {acsConnectionString}");

    foreach (var PhoneNumber in request.PhoneNumbers)
    {
        try
        {
            PhoneNumberIdentifier target = new PhoneNumberIdentifier(PhoneNumber);
            PhoneNumberIdentifier caller = new PhoneNumberIdentifier(acsPhoneNumber);

            Console.WriteLine($"Received outbound call trigger for phone number :{PhoneNumber}");

            CallInvite callInvite = new CallInvite(target, caller);

            var callbackUri = new Uri(new Uri(appBaseUrl), $"/api/callbacks/{Guid.NewGuid()}?callerId={PhoneNumber}");
            logger.LogInformation($"Callback Url: {callbackUri}");
            var websocketUri = appBaseUrl.Replace("https", "wss") + "/ws";
            logger.LogInformation($"WebSocket Url: {websocketUri}");

            var mediaStreamingOptions = new MediaStreamingOptions(
                transportUri: new Uri(websocketUri),
                contentType: MediaStreamingContent.Audio,
                audioChannelType: MediaStreamingAudioChannel.Mixed,
                startMediaStreaming: true
            )
            {
                EnableBidirectional = true,
                AudioFormat = AudioFormat.Pcm24KMono
            };

            var createCallOptions = new CreateCallOptions(callInvite, callbackUri)
            {
                MediaStreamingOptions = mediaStreamingOptions,
                //CallIntelligenceOptions = new CallIntelligenceOptions()
                //{
                //    //CognitiveServicesEndpoint = new Uri("https://tf-ai-aivoice-dev-ai-voice-rkvm.cognitiveservices.azure.com/")
                //}
            };

            CreateCallResult createCallResult = await client.CreateCallAsync(createCallOptions);
            logger.LogInformation($"Started call for connection id: {createCallResult.CallConnection.CallConnectionId}");
            return Results.Ok($"{createCallResult.CallConnection.CallConnectionId} - {createCallResult.CallConnectionProperties.CallConnectionState} - {createCallResult.CallConnectionProperties.CallbackUri}"); 
        }
        catch (Exception ex)
        {
            Console.WriteLine($"Error initiating outbound call: {ex.Message}");
            return Results.Problem(ex.Message);
        }
    }
    return Results.Ok(">> Outbound calls initiated successfully");
});



app.MapPost("/api/incomingCall", async (
    [FromBody] EventGridEvent[] eventGridEvents,
    ILogger<Program> logger) =>
{
    foreach (var eventGridEvent in eventGridEvents)
    {
        Console.WriteLine($"Incoming Call event received.");

        // Handle system events
        if (eventGridEvent.TryGetSystemEventData(out object eventData))
        {
            // Handle the subscription validation event.
            if (eventData is SubscriptionValidationEventData subscriptionValidationEventData)
            {
                var responseData = new SubscriptionValidationResponse
                {
                    ValidationResponse = subscriptionValidationEventData.ValidationCode
                };
                return Results.Ok(responseData);
            }
        }

        var jsonObject = Helper.GetJsonObject(eventGridEvent.Data);
        var callerId = Helper.GetCallerId(jsonObject);
        var incomingCallContext = Helper.GetIncomingCallContext(jsonObject);
        var callbackUri = new Uri(new Uri(appBaseUrl), $"/api/callbacks/{Guid.NewGuid()}?callerId={callerId}");
        logger.LogInformation($"Callback Url: {callbackUri}");
        var websocketUri = appBaseUrl.Replace("https", "wss") + "/ws";
        logger.LogInformation($"WebSocket Url: {callbackUri}");

        var mediaStreamingOptions = new MediaStreamingOptions(
                new Uri(websocketUri),
                MediaStreamingContent.Audio,
                MediaStreamingAudioChannel.Mixed,
                startMediaStreaming: true
                )
        {
            EnableBidirectional = true,
            AudioFormat = AudioFormat.Pcm24KMono
        };
      
        var options = new AnswerCallOptions(incomingCallContext, callbackUri)
        {
            MediaStreamingOptions = mediaStreamingOptions,
        };

        AnswerCallResult answerCallResult = await client.AnswerCallAsync(options);
        logger.LogInformation($"Answered call for connection id: {answerCallResult.CallConnection.CallConnectionId}");
    }
    return Results.Ok();
});

// api to handle call back events
app.MapPost("/api/callbacks/{contextId}", async (
    [FromBody] CloudEvent[] cloudEvents,
    [FromRoute] string contextId,
    [Required] string callerId,
    ILogger<Program> logger) =>
{
    foreach (var cloudEvent in cloudEvents)
    {
        CallAutomationEventBase @event = CallAutomationEventParser.Parse(cloudEvent);
        logger.LogInformation($"Event received: {JsonConvert.SerializeObject(@event, Formatting.Indented)}");
    }

    return Results.Ok();
});

app.UseWebSockets();

app.Use(async (context, next) =>
{
    if (context.Request.Path == "/ws")
    {
        if (context.WebSockets.IsWebSocketRequest)
        {
            try
            {
                var webSocket = await context.WebSockets.AcceptWebSocketAsync();
                var mediaService = new AcsMediaStreamingHandler(webSocket, builder.Configuration);

                // Set the single WebSocket connection
                await mediaService.ProcessWebSocketAsync();
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Exception received {ex}");
            }
        }
        else
        {
            context.Response.StatusCode = StatusCodes.Status400BadRequest;
        }
    }
    else
    {
        await next(context);
    }
});

app.Run();