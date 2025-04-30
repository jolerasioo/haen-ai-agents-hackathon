using System.ComponentModel;
using Newtonsoft.Json;

namespace acstalk.Models;

public class SendSmsRequest
{
    [JsonProperty("target_phone_numbers"), Description("Must be a valid phone number in E.164 format")]
    public required string[] TargetPhoneNumbers { get; set; } // Must be a valid phone number in E.164 format

    [JsonProperty("new_alert_data")]
    public string NewAlertData { get; set; } = string.Empty;

    // optional additional data
    [JsonProperty("additional_data")]
    public string AdditionalData { get; set; } = string.Empty; 
}
