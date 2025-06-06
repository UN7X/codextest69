# codextest69 Uploader

A simple Flask-based file and text sharing service.

## Features
- Guest uploads up to 10 MB
- Registered users uploads up to 40 MB
- Pastebin-like text sharing with editing
- Admin dashboard to monitor users and files
- Default admin login: `admin` / `root`
- Rate limited endpoints

## Development
Install dependencies and run:
```bash
pip install -r requirements.txt
python -m app.main
```

## Testing
Run the unit tests with:
```bash
pytest
```
