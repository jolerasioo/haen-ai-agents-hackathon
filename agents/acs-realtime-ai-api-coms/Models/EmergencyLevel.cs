using System;
using Azure.Core.GeoJson;

namespace acstalk.Models;

public class EmergencyAlert
{
    public string emergencyLevel { get; set; }
    public string emergencyMessage { get; set; }
    public string locationCoordinates { get; set; }
    public string citizenId { get; set; }
    public string phoneNumber { get; set; }
    
}

public enum EmergencyLevel
{
    LOW,
    MEDIUM,
    SEVERE
}