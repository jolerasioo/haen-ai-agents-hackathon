# PROTOCOL RAG AGENT
By using Azure AI Agent Service, we can connect our agent to an Azure Search Service Index to perform the RAG pattern. For this case, given the complexity of the data (PDF, complex language, multiple files), we decided to go for `HYBRID SEMANTIC SEARCH` to ensure advance search capabilities to address it.

1. We created the Index directly on the portal for effienciy, but on a real scenario we would add a data pipeline following proper DevOps practices.
0. Once the index is built, we connected it to our connection resource on AI Foundry, adding it as an index to make accessible. Again, this would all be managed by code on a real scenario.
0. The code handles the creation of the agent, but in our case, configured it on AI Foundry Agents tab, adding the index as a Knowledge Source and adding the system prompt. The code creates the agent if it doesn't exist anyway.
0. The function retrieves the agent and passes the new query for the AI Agent to produce answers. Here's a sample output to the query *What are the main evacuation options for Valencia?*:


```HTTP/1.1 200 OK
Connection: close
Content-Type: text/plain; charset=utf-8
Date: Wed, 30 Apr 2025 14:27:12 GMT
Server: Kestrel
Transfer-Encoding: chunked

The primary evacuation options for Valencia during severe flooding are outlined in a detailed emergency protocol:

1. **Evacuation Zones & Staging Areas**:
   - Municipalities maintain updated maps of designated evacuation zones and staging areas. These are categorized geographically (e.g., Valencia North, South & Coast, Rural Uplands) for organized movement and shelter allocation【3:0†source】.

2. **Transport Coordination**:
   - AI-supported systems track live road conditions, suggesting alternate routes to minimize congestion and delays. Municipal transport assets are registered to ensure efficient allocation during evacuations【3:1†source】.

3. **Activation Criteria**:
   - Evacuations are triggered when specific thresholds are met, such as water levels exceeding 1.2 meters, rapid water rise alerts, or red-level flood warnings issued by AEMET【3:0†source】.

4. **Resource Deployment**:
   - Emergency stockpiles include portable water pumps, tents, food kits, and medical supplies. These resources are dispatched within hours of a Red Alert activation to support evacuation efforts【3:2†source】【3:4†source】.

5. **Communication and Coordination**:
   - Municipal authorities manage local evacuations and shelters, while regional authorities coordinate inter-agency logistics and medical responses. National-level support includes military assistance if necessary【3:3†source】【3:4†source】.

These measures aim for rapid response, minimizing risk to life and infrastructure.```