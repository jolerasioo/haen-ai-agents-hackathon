# ACS Talk 

## Project Overview

ACS Talk is an ASP.NET Core application designed to provide a virtual agent that helps Sainsbury's customers with their questions. The virtual agent provides information, routes questions to the relevant area, and ensures a polite, concise, and informative interaction.

## Main Features

- Integration with Azure Communication Services (ACS) for handling calls.
- Integration with Azure OpenAI Service for real-time conversation and AI responses.
- WebSocket communication for media streaming.
- Configurable settings for different environments.

## Deployment Instructions

To deploy the Agentic ACS application to Azure Web Apps, follow these steps:

1. **Create an Azure Communication Resource**:
   - Go to the Azure portal and create a new ACS.
   - Configure the necessary settings such as resource group, app name, and region.


## Configuration and Settings

The application requires the following configurations and settings:

1. **.config/dotnet-tools.json**:
   - This file sets up the .NET tools required for the project.

2. **appsettings.json** and **appsettings.Development.json**:
   - These files contain various settings and configurations for the application.
   - Update the `AcsConnectionString`, `AzureOpenAIServiceKey`, `AzureOpenAIServiceEndpoint`, and other relevant settings.

3. **.vscode/settings.json**:
   - This file contains settings for deploying the application using Visual Studio Code.

## Local Development Instructions

To set up the Agentic ACS application for local development, follow these steps:

1. **Install .NET Core SDK**:
   - Ensure that you have the .NET Core SDK (dotnet v9.0.2) installed on your machine. You can download it from the official .NET website: https://dotnet.microsoft.com/download

2. **Clone the Repository**:
   - Clone the repository to your local machine using the following command:
     ```sh
     git clone https://github.com/simonthurman/acstalk.git
     ```

3. **Set Up Dev Tunnel**:
   - Create a dev tunnel for a webhook that is accessing port 5166. You can use tools like ngrok or Azure Dev Tunnels to create the tunnel.
   - Update the `DevTunnelUri` setting in the `appsettings.Development.json` file with the URL of the dev tunnel.
     ```sh
     devtunnel create --allow-anonymous 
     devtunnel port create -p 5166
     devtunnel host
     ```
4. **Run the Application**:
   - Update the app settings with the url for the dev tunnel.
   - Build and run the application.  

5. **Create Event Grid Subscription**:
   - Create an Event Grid subscription for the incoming call event in the Azure Communication Services resource.
   - Configure the Event Grid subscription to send events to a webhook and use the dev tunnel's URL and suffix the url with `api/incomingCall`.

You should have a running local app, a web tunnel exposing it to the internet, and an ACS resource able to communicate with it.
