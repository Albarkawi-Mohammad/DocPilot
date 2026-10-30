# DocPilot

A desktop prototype for making household paperwork easier to manage.

DocPilot brings PDF import, document search, review decisions, and an archive view into one Windows app. The idea is to help people keep letters, insurance paperwork, bank statements, and other documents organised by person and category, with a clear place to check anything that needs attention.

**Current status: interactive UI preview.** The interface works with fictional sample records and a simulated processing pipeline. Real OCR, AI classification, scanning, and automatic filing are future work.

## What does it do?

- **Dashboard:** see document counts, pending reviews, and recent demo activity.
- **Scan & Import:** select or drop PDFs, check the queue, and read page counts locally where supported.
- **Processing:** explore an eight-stage workflow, from import through OCR and classification to archiving, with start, pause, resume, and cancel controls. These stages are simulated.
- **Documents:** search and filter sample records by person, category, and status, and inspect their details.
- **Review Center:** assign an unknown person, choose a category, or decide whether pages belong together. Decisions update the demo immediately.
- **Archive:** browse a logical person-and-category view of the sample documents.
- **Settings:** edit demo profiles and categories and switch between dark and light themes.

## How does it help?

Household paperwork can end up scattered across folders and mixed between family members. DocPilot demonstrates a more consistent workflow: bring documents in, check uncertain results, and find them again through one organised interface.

The prototype makes that workflow easy to try before building the processing backend. It is useful for demonstrating the product idea, gathering feedback, and developing a future local document-management tool. It does not yet organise real files automatically.

## Privacy and current limits

- Sample records are fictional; no personal documents are included in the repository.
- Selected PDFs stay on your computer. The app reads their page counts locally and keeps their paths in memory.
- Original files are not copied, moved, renamed, deleted, or modified.
- No network calls, telemetry, cloud processing, or active external integrations are implemented.
- Document previews are placeholders. OCR, AI, scanner access, Ollama, and Paperless-ngx are not connected.
- Processing results, review decisions, and settings are session-only and reset when the app closes.
- The archive is a visual demo; it does not create folders or write documents to disk.

## Run locally

Built with Python and PySide6. Windows is the primary target. Use Python 3.10 or newer.

From the project folder:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe main.py
```

Installing dependencies requires internet access. The preview itself runs offline.

## Try the demo

1. Start with the Dashboard and browse the sample documents.
2. Open Scan & Import and select a non-sensitive PDF to try the queue.
3. Start the simulated processing run and try pausing or cancelling it.
4. Resolve a question in Review Center, then check the updated document and archive views.
5. Change a demo profile or category in Settings and try both themes.

## Build a Windows executable

```powershell
.\.venv\Scripts\python.exe -m pip install pyinstaller
.\.venv\Scripts\python.exe -m PyInstaller --noconfirm --clean DocPilot.spec
```

The output is `dist\DocPilot\DocPilot.exe`. Keep the whole `dist\DocPilot` folder together because the executable needs its bundled runtime and assets. Build outputs and the local virtual environment are not included in this repository.

## Project structure

```text
main.py              Application entry point
requirements.txt     Runtime dependency
DocPilot.spec        Windows packaging recipe
app/
  assets/            Icons and theme assets
  data/              Fictional sample records
  models/            Document and review models
  pages/             The seven application screens
  services/          In-memory state, demo pipeline, PDF metadata, backend protocols
  theme/             Shared colours and styles
  widgets/           Reusable interface components
```

`AppState` keeps the demo data in memory and notifies the interface when it changes. `DemoProcessingService` runs the simulated pipeline. Backend protocols in `app/services/contracts.py` provide extension points for future processing, storage, and integrations.

## Future direction

Potential next steps include persistent storage, real PDF previews, OCR, local AI classification, scanner support, and an archive backend. These are planned directions, not features available in this preview.
