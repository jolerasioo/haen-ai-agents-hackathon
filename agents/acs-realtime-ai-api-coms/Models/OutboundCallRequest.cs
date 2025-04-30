using System;
using System.ComponentModel;
using System.Text.Json.Serialization; 

namespace acstalk.Models;

public class OutboundCallRequest
{

    [JsonPropertyName("phone_numbers"), Description("Must be an array of valid phone number in E.164 format")]
    public required string[] PhoneNumbers { get; set; } // The phone number to call
    [JsonPropertyName("citizen_name")]
    public required string CitizenName { get; set; } // The name of the citizen to call
    [JsonPropertyName("citizen_id")]
    public required string CitizenId { get; set; } // The ID of the citizen to call
    [JsonPropertyName("language"), Description("The language to use for the call (default is English)")]
    public string Language { get; set; } = "English"; // The language to use for the call (default is English)
    [JsonPropertyName("new_alert_data")]
    public required string NewAlertData { get; set; }

}
