![image](https://user-images.githubusercontent.com/42340621/224944259-1ddb0bcb-7e67-4424-b6db-2300435dafb0.png)
## Introduction
The goal of this project is to provide a real time tracking on the flights by displaying their current status and also draw their path on a map.
We will also provide statistiques data on the most frequently used airlines / airporsts per each continent.

## tech stack
### Data Sources
Web Scraping Wikipedia  
https://airlabs.co/

### Data Storage
Mongodb cloud

### Data Processing and Visualizations
Pandas  
Plotly  
Dash

## Deployment
1. Clone the project  
git clone

2. Create and activate a virtual env  
python3 -m venv env;source env/bin/activate

3.Run the docker-compose.yml in a terminale  
This will take a bit to build and deploy the two containers used to run the application.

4. Open your browser at the URL
http://127.0.0.1:8055/