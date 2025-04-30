using System.Net.WebSockets;
using System.ComponentModel;
using System.Threading.Channels;
using OpenAI.RealtimeConversation;
using Azure.AI.OpenAI;
using System.ClientModel;
using Azure.Communication.CallAutomation;
using CliWrap.Builders;
using System.Text.Json;
using Azure.Core.GeoJson;
using acstalk.Models;

#pragma warning disable OPENAI002
namespace CallAutomationOpenAI
{
    //public class EmergencyAlert
    //{
    //    public string emergencyLevel { get; set; }
    //    public string emergencyMessage { get; set; }
    //    public string locationCoordinates { get; set; }
    //    public string citizenId { get; set; }
    //    public string phoneNumber { get; set; }
    //    
    //}
    //
    //public enum EmergencyLevel
    //{
    //    LOW,
    //    MEDIUM,
    //    SEVERE
    //}

    public class AzureOpenAIService
    {
        private WebSocket m_webSocket;
        private CancellationTokenSource m_cts;
        private RealtimeConversationSession m_aiSession;
        private AcsMediaStreamingHandler m_mediaStreaming;
        private MemoryStream m_memoryStream;
        private string m_answerPromptSystemTemplate;
        private static string m_payloadData = string.Empty;

        public static void UpdateSystemPromptTemplate(string messageToAppend)
        {
            //var _m_answerPromptSystemTemplate = File.ReadAllText("AnswerPromptSystemTemplate.txt");

            m_payloadData = m_payloadData + "\n## DATA:\n" + messageToAppend;
        }

        public AzureOpenAIService(AcsMediaStreamingHandler mediaStreaming, IConfiguration configuration)
        {
            m_mediaStreaming = mediaStreaming;
            m_cts = new CancellationTokenSource();
            m_aiSession = CreateAISessionAsync(configuration).GetAwaiter().GetResult();
            m_memoryStream = new MemoryStream();
            m_answerPromptSystemTemplate = string.Empty;
            m_payloadData = string.Empty;
        }

        private async Task<RealtimeConversationSession> CreateAISessionAsync(IConfiguration configuration)
        {
            var openAiKey = configuration.GetValue<string>("AzureOpenAIServiceKey");
            ArgumentNullException.ThrowIfNullOrEmpty(openAiKey);

            var openAiUri = configuration.GetValue<string>("AzureOpenAIServiceEndpoint");
            ArgumentNullException.ThrowIfNullOrEmpty(openAiUri);

            var openAiModelName = configuration.GetValue<string>("AzureOpenAIDeploymentModelName");
            ArgumentNullException.ThrowIfNullOrEmpty(openAiModelName);

            var baseSystemPrompt = configuration.GetValue<string>("BaseSystemPrompt") ??File.ReadAllText("AnswerPromptSystemTemplate.txt");
            var systemPrompt = baseSystemPrompt + m_payloadData;
            ArgumentNullException.ThrowIfNullOrEmpty(openAiUri);

            Console.WriteLine($"OpenAI Endpoint: {openAiUri}");
            Console.WriteLine($"OpenAI Key: {openAiKey}");
            Console.WriteLine($"OpenAI Model Name: {openAiModelName}");


            var aiClient = new AzureOpenAIClient(new Uri(openAiUri), new ApiKeyCredential(openAiKey));
            var RealtimeCovnClient = aiClient.GetRealtimeConversationClient(openAiModelName);
            var session = await RealtimeCovnClient.StartConversationSessionAsync();

            // Session options control connection-wide behavior shared across all conversations,
            // including audio input format and voice activity detection settings.
            ConversationSessionOptions sessionOptions = new()
            {
                Instructions = systemPrompt,
                Voice = ConversationVoice.Echo,
                Tools = { RaiseEmergencyAlertIntoSystem() },
                InputAudioFormat = ConversationAudioFormat.Pcm16,
                OutputAudioFormat = ConversationAudioFormat.Pcm16,
                InputTranscriptionOptions = new()
                {
                    Model = "whisper-1",
                },
                TurnDetectionOptions = ConversationTurnDetectionOptions.CreateServerVoiceActivityTurnDetectionOptions(0.5f, TimeSpan.FromMilliseconds(500), TimeSpan.FromMilliseconds(500)),
            };

            await session.ConfigureSessionAsync(sessionOptions);
            // get user profile here
            await session.AddItemAsync(
                ConversationItem.CreateUserMessage([GetIntroduction()]));
            return session;
        }

        // Loop and wait for the AI response
        private async Task GetOpenAiStreamResponseAsync()
        {
            try
            {
                await m_aiSession.StartResponseAsync();
                await foreach (ConversationUpdate update in m_aiSession.ReceiveUpdatesAsync(m_cts.Token))
                {
                    if (update is ConversationSessionStartedUpdate sessionStartedUpdate)
                    {
                        Console.WriteLine($"<<< Session started. ID: {sessionStartedUpdate.SessionId}");
                        Console.WriteLine();
                    }

                    if (update is ConversationInputSpeechStartedUpdate speechStartedUpdate)
                    {
                        Console.WriteLine(
                            $"  -- Voice activity detection started at {speechStartedUpdate.AudioStartTime} ms");
                        // Barge-in, send stop audio
                        var jsonString = OutStreamingData.GetStopAudioForOutbound();
                        await m_mediaStreaming.SendMessageAsync(jsonString);
                    }

                    if (update is ConversationInputSpeechFinishedUpdate speechFinishedUpdate)
                    {
                        Console.WriteLine(
                            $"  -- Voice activity detection ended at {speechFinishedUpdate.AudioEndTime} ms");
                    }

                    // Item finished updates arrive when all streamed data for an item has arrived and the
                    // accumulated results are available. In the case of function calls, this is the point
                    // where all arguments are expected to be present.
                    if (update is ConversationItemStreamingFinishedUpdate itemFinishedUpdate)
                    {
                        Console.WriteLine();

                        if (itemFinishedUpdate.FunctionCallId is not null)
                        {
                            Console.WriteLine($"    + Responding to tool invoked by item: {itemFinishedUpdate.FunctionName}");
                            string parameters = itemFinishedUpdate.FunctionCallArguments;
                            string functionName = itemFinishedUpdate.FunctionName;
                            string toolOutput = string.Empty;
                            switch (functionName)
                            {
                                case "raise_emergency_alert":
                                    Console.WriteLine($"    + Tool parameters: {parameters}");
                                    // Set up JsonSerializerOptions to ignore case
                                    var options = new JsonSerializerOptions
                                    {
                                        PropertyNameCaseInsensitive = true
                                    };

                                    // Deserialize the JSON string into a JobOfferParameters object
                                    EmergencyAlert alert = JsonSerializer.Deserialize<EmergencyAlert>(parameters, options);
                                    //// Extract the values
                                    string emergencyLevel = alert.emergencyLevel;
                                    string msg = alert.emergencyMessage;
                                    string locationCoordinates = alert.locationCoordinates;
                                    string citizenId = alert.citizenId;
                                    string phone = alert.phoneNumber;

                                    // run tool
                                    toolOutput = await RaiseEmergencyAlert(
                                        emergencyLevel,
                                        msg,
                                        locationCoordinates,
                                        citizenId,
                                        phone
                                    );
                                    Console.WriteLine($"    + Tool parameters: {parameters}");
                                    break;
                                default:
                                    Console.WriteLine($"    + Tool parameters: {parameters}");
                                    break;
                            }

                            ConversationItem functionOutputItem = ConversationItem.CreateFunctionCallOutput(
                                callId: itemFinishedUpdate.FunctionCallId,
                                output: toolOutput);

                            await m_aiSession.AddItemAsync(functionOutputItem);
                        }
                        else if (itemFinishedUpdate.MessageContentParts?.Count > 0)
                        {
                            Console.Write($"    + [{itemFinishedUpdate.MessageRole}]: ");
                            foreach (ConversationContentPart contentPart in itemFinishedUpdate.MessageContentParts)
                            {
                                Console.Write(contentPart.AudioTranscript);
                            }
                            Console.WriteLine();
                        }
                        Console.WriteLine($"  -- Item streaming finished, response_id={itemFinishedUpdate.ResponseId}");
                    }


                    if (update is ConversationItemStreamingStartedUpdate itemStartedUpdate)
                    {
                        Console.WriteLine($"  -- Begin streaming of new item");
                        if (!string.IsNullOrEmpty(itemStartedUpdate.FunctionName))
                        {
                            Console.Write($"    {itemStartedUpdate.FunctionName}: ");
                        }
                    }

                    // Audio transcript  updates contain the incremental text matching the generated
                    // output audio.
                    if (update is ConversationItemStreamingAudioTranscriptionFinishedUpdate outputTranscriptDeltaUpdate)
                    {
                        Console.Write(outputTranscriptDeltaUpdate.Transcript);
                    }

                    // Audio delta updates contain the incremental binary audio data of the generated output
                    // audio, matching the output audio format configured for the session.
                    if (update is ConversationItemStreamingPartDeltaUpdate deltaUpdate)
                    {
                        if (deltaUpdate.AudioBytes != null)
                        {
                            Console.Write(deltaUpdate.FunctionArguments);
                            var jsonString = OutStreamingData.GetAudioDataForOutbound(deltaUpdate.AudioBytes.ToArray());
                            await m_mediaStreaming.SendMessageAsync(jsonString);
                        }
                    }

                    if (update is ConversationItemStreamingTextFinishedUpdate itemFinishedTextUpdate)
                    {
                        Console.WriteLine();
                        Console.WriteLine($"  -- Item streaming finished, response_id={itemFinishedTextUpdate.ResponseId}");
                    }

                    if (update is ConversationInputTranscriptionFinishedUpdate transcriptionCompletedUpdate)
                    {
                        Console.WriteLine();
                        Console.WriteLine($"  -- User audio transcript: {transcriptionCompletedUpdate.Transcript}");
                        Console.WriteLine();
                    }

                    if (update is ConversationResponseFinishedUpdate turnFinishedUpdate)
                    {
                        Console.WriteLine($"  -- Model turn generation finished. Status: {turnFinishedUpdate.Status}");

                        // Here, if we processed tool calls in the course of the model turn, we finish the
                        // client turn to resume model generation. The next model turn will reflect the tool
                        // responses that were already provided.
                        if (turnFinishedUpdate.CreatedItems.Any(item => item.FunctionName?.Length > 0))
                        {
                            Console.WriteLine($"  -- Ending client turn for pending tool responses");
                            await m_aiSession.StartResponseAsync();
                        }
                    }

                    if (update is ConversationErrorUpdate errorUpdate)
                    {
                        Console.WriteLine();
                        Console.WriteLine($"ERROR: {errorUpdate.Message}");
                        break;
                    }
                }
            }
            catch (OperationCanceledException e)
            {
                Console.WriteLine($"{nameof(OperationCanceledException)} thrown with message: {e.Message}");
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Exception during ai streaming -> {ex}");
            }
        }

        public void StartConversation()
        {
            _ = Task.Run(async () => await GetOpenAiStreamResponseAsync());
        }

        public async Task SendAudioToExternalAI(MemoryStream memoryStream)
        {
            await m_aiSession.SendInputAudioAsync(memoryStream);
        }

        public void Close()
        {
            m_cts.Cancel();
            m_cts.Dispose();
            m_aiSession.Dispose();
        }

        private static ConversationFunctionTool RaiseEmergencyAlertIntoSystem()
        {
            return new ConversationFunctionTool()
            {
                Name = "raise_emergency_alert",
                Description = "This tool is used when an emergency is detected during the conversation with the citizen. Emergencies can be STRANDED_ALONE, MEDICAL_NEED, UNABLE_TO_EVACUATE, LACK_OF_MEDICATION, NO_FOOD_OR_WATER, POWER_DEPENDENT, DISPLACED, MENTAL_DISTRESS, MISSING_CAREGIVER, LANGUAGE_BARRIER, MOBILITY_ISSUES, SAFETY_THREAT, ISOLATED, OTHER.",
                Parameters = BinaryData.FromString("""
            {
              "type": "object",
              "properties": {
                "emergencyLevel": {
                  "type": "string",
                  "description": "The emergency level with the options being: LOW, MEDIUM, SEVERE"
                },
                "emergencyMessage": {
                  "type": "string",
                  "description": "Very short message to add to the alert to show the alert type."
                },
                "locationCoordinates": {
                  "type": "string",
                  "description": "Approximate coordinates of the location of the citizen that you can figure out based on the address."
                },
                "citizenId": {
                  "type": "string",
                  "description": "A citizen ID code, could be passport or ID card."
                },
                "phoneNumber": {
                  "type": "string",
                  "description": "A phone number to contact the citizen."
                }
              },
              "required": [
                "emergencyLevel",
                "emergencyMessage",
                "locationCoordinates",
                "citizenId",
                "phoneNumber"
              ]
            }
            """)
            };
        }

        public async Task<string> RaiseEmergencyAlert(
            [Description("the emergency level for the system")] string emergencyLevel,
            [Description("Emergency message to add to the alert, a very brief one")] string emergencyMessage,
            [Description("Approximate coordinates of the location of the citizen")] string locationCoordinates,
            [Description("A citizen ID code, could be passport or ID card")] string citizenId,
            [Description("A phone number to contact the citizen")] string phoneNumber
        )
        {
            try
            {
                // Validate the parameters here if needed
                if (string.IsNullOrEmpty(emergencyMessage) || string.IsNullOrEmpty(citizenId) || string.IsNullOrEmpty(phoneNumber))
                {
                    throw new ArgumentException("Emergency message, citizen ID, and phone number are required.");
                }
                // Simulate raising an asyncronous post call to a cosmos db so that there's an await
                await Task.Delay(100);

                var timeLog = DateTime.UtcNow.ToString("yyyy-MM-ddTHH:mm:ssZ");

                Console.WriteLine($"Emergency Level: {emergencyLevel}, Log datetime: {timeLog}, Message: {emergencyMessage}, Location: {locationCoordinates}, Citizen ID: {citizenId}, Phone: {phoneNumber}");
                return "OK 200: Emergency alert raised successfully.";

            }
            catch (Exception ex)
            {
                Console.WriteLine($"Error: {ex.Message}");
                return "Error: " + ex.Message;
            }
        }



        private string GetIntroduction()
        {
            return "Hello, I am your AI assistant. How may I help you today?";
        }

        private string GetCustomerDetails()
        {
            return "Can you please provide your name and email address?";
        }

        private static string QuestionResolved(string customerName, string customerEmail)
        {
            Console.WriteLine($"Customer name: {customerName}, your issue has been resolved.");
            return $"Thank you {customerName} at {customerEmail}. The resolution has been successfully completed.";
        }

    }
}