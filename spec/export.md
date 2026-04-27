Goal:
- Python script to export a list of all downloaded movies from Radarr to either a csv or json file
- Only downloaded movies are included
- Each movie info must include:
    - Radarr link to movie
    - Title
    - Genre
    - Quality
    - Resolution
    - Format

Languages:
- python3.11+

Script Parameters:

- --radarr-url: the url if the radarr instance
- --export-format: csv or json
- --export-filename: Path for the script to write data to
    - Note: Path can be either absolute or relative to user's current directory

Authentication:
- The radarr api key is stored in an environment variable RADARR_API_KEY

Output:

- A csv or json file containing the export data depending on export-format parameter