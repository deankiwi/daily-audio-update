# daily-audio-update

An automated personal briefing system that generates a daily MP3 podcast covering market data, tech news, world news, and weather. The briefing is narrated in Spanish (or your target language) via OpenAI to help with language learning, and automatically uploaded to Google Cloud Storage.

## Architecture

```mermaid
graph TD
    Start([⏱️ 6am auto kickoff]) --> Plugins
    
    subgraph "Data Collection"
        Plugins --> |Fetch| Market["📈 Market Data<br/>(Yahoo Finance)"]
        Plugins --> |Fetch| Tech["💻 Tech News<br/>(Hacker News)"]
        Plugins --> |Fetch| BBC["🌍 World News<br/>(BBC)"]
        Plugins --> |Fetch| Weather["🌤️ Weather<br/>(OpenWeatherMap)"]
    end
    
    Market --> Aggregator[Data Aggregator]
    Tech --> Aggregator
    BBC --> Aggregator
    Weather --> Aggregator
    
    Aggregator --> LLM["🤖 LLM Script Generator<br/>(OpenAI GPT-4)"]
    
    LLM --> |"Generate Script (Spanish)"| Script[Briefing Script]
    
    Script --> TTS["🗣️ Audio Synthesizer<br/>(OpenAI TTS)"]
    
    TTS --> |"Generate MP3"| AudioFile[Audio File]
    
    AudioFile --> GCS["☁️ Google Cloud Storage"]
    
    GCS --> |"Stream"| User((User))
    
    classDef blue fill:#e1f5fe,stroke:#01579b,stroke-width:2px;
    classDef green fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px;
    classDef orange fill:#fff3e0,stroke:#ef6c00,stroke-width:2px;
    
    class Market,Tech,BBC,Weather blue;
    class LLM,TTS green;
    class GCS,User orange;
```

## Features

- **Personalized Data**: Fetches specific data points you care about (Stocks, Tech, Weather).
- **Language Learning**: Translates the briefing into your target language (default: Spanish).
- **High-Quality Audio**: Uses OpenAI's TTS for natural-sounding narration.
- **cloud Access**: Uploads to Google Cloud Storage for easy access via specific or "latest" links.

## Usage

1.  Configure `.env` with API keys and preferences.
2.  Run the main script:
    ```bash
    uv run main.py
    ```
