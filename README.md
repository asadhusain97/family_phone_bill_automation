# T-Mobile Bill Parser for iOS

A Python script that parses T-Mobile PDF bills and splits costs among family members. Designed to run locally on iPhone using a-Shell with iOS Share Sheet integration.

## What is this

Learn more [here](https://asadhusain97.github.io/projects/mobilefamilybill.html)

This tool takes a T-Mobile bill PDF and outputs a formatted summary showing how much each family member owes. Perfect for splitting family plan bills fairly and quickly.

## Features

- **PDF Parsing**: Extracts billing data directly from T-Mobile PDF bills using pypdf (pure Python, no C compiler needed)
- **Smart Cost Allocation**: Two strategies for dividing plan costs
  - Equal split: Divide total plan cost equally among all members
  - Tiered split: Base plan shared among "included" members, others pay their individual rate
- **Equipment & Services**: Properly attributes device payments and add-on services to each member
- **iOS Native**: Runs on iPhone via a-Shell terminal app (no C dependencies)
- **Share Sheet Integration**: Process bills instantly from any app using iOS Shortcuts
- **Clean Output**: Easy-to-read format with dot leaders between names and totals, perfect for Apple Notes or Messages

## How I Use It

1. T-Mobile emails me the monthly bill
2. Open the PDF in Mail app
3. Tap Share → Run my Shortcut
4. Bill summary appears in Apple Notes instantly

No cloud services, no email automation, no waiting. Just instant bill splitting on my phone.

## Setup

### Prerequisites

- iPhone or iPad with iOS 13+
- [a-Shell](https://apps.apple.com/us/app/a-shell/id1473805438) app (free on App Store)
- [Working Copy](https://apps.apple.com/us/app/working-copy-git-client/id896694807) or similar (for cloning repo to iOS)

### Installation

1. **Install a-Shell** from the App Store

2. **Clone this repository** to your iPhone using Working Copy or download/transfer files manually

3. **Install Python dependencies** in a-Shell:
   ```bash
   cd ~/Documents/family_phone_bill_automation
   pip install -r requirements.txt
   ```

4. **Configure your family plan** in `configs.yml`:
   ```yaml
   family_count: 10  # Your number of family members
   plan_cost_for_all_members: True  # True = equal split, False = tiered split
   ```

5. **Optional: Map phone numbers to names** by creating a `.env` file:
   ```bash
   # Copy the example file and edit with your phone numbers
   cp .env.example .env
   # Then edit .env with your actual phone numbers and names
   ```

   Or create from scratch:
   ```bash
   cat > .env << 'EOF'
   MEMBER_NAMES = {"(999) 637-3009": "Mom", "(999) 637-5007": "Dad", "(999) 637-3003": "Sister"}
   EOF
   ```

   The script will automatically load this file and display names instead of phone numbers in the output.

   **Important:** Phone numbers must match EXACTLY as they appear in your PDF, including spaces and parentheses.

### Test Installation

```bash
python main.py ./example_bill_summary/T-Mobile\ Bill_example.pdf
```

You should see a formatted table with member names and totals.

## Usage

### Command Line

```bash
python main.py /path/to/bill.pdf
```

### iOS Shortcuts Integration

Create an iOS Shortcut to process bills from the Share Sheet:

1. **Create a new Shortcut** with these actions:

   - **Receive** "PDFs" input from Share Sheet
   - **Save File** to `a-Shell/Documents/bill.pdf` (overwrite if exists)
   - **Run Script Over SSH** or **Open URLs** with:
     ```
     ashell://cd ~/Documents/family_phone_bill_automation && python main.py ~/Documents/bill.pdf
     ```
   - **Get** output from Shell Script
   - **Create Note** in Apple Notes with the text output
   - Optional: **Show Notification** with "Bill processed!"

2. **Configure Shortcut settings**:
   - Enable "Show in Share Sheet"
   - Accept "Files" and "PDFs" as input types
   - Name it something memorable like "Split Bill"

3. **Usage flow**:
   - Open T-Mobile bill PDF in any app (Mail, Files, etc.)
   - Tap Share button
   - Select "Split Bill" shortcut
   - Bill summary appears in Notes within seconds

## Output Format

### With Name Mapping (.env file configured)

```
T-Mobile Bill Summary for January

Raina ............................. $32.53
Dhoni ............................. $48.62
Yuvraj ............................ $32.00
Sachin ............................ $32.00
Laxman ............................ $32.00
Navjot ............................ $32.00
Sunil ............................. $34.53
Rohit ............................. $32.28
Shikhar ........................... $13.66
Shubhman .......................... $32.56

Grand Total ...................... $322.18
```

### Without Name Mapping (falls back to phone numbers)

```
T-Mobile Bill Summary for January

(999) 637-3009 .................... $32.53
(999) 637-5007 .................... $48.62
(999) 637-3003 .................... $32.00
(999) 637-5000 .................... $32.00
(999) 909-4005 .................... $32.00
(999) 746-9006 .................... $32.00
(999) 533-9000 .................... $34.53
(999) 275-8001 .................... $32.28
(999) 476-6003 .................... $13.66
(999) 433-6001 .................... $32.56

Grand Total ...................... $322.18
```

## Configuration

### configs.yml

```yaml
# Number of family members in your plan
family_count: 10

# Cost allocation strategy
plan_cost_for_all_members: True

# PDF page with billing summary (usually page 1)
page_number: 1

# Output file location
summarized_bill_path: "attachments/summary.csv"
```

### .env (Name Mapping)

**Optional** - Create a `.env` file to map phone numbers to friendly names:

```bash
# .env file format
MEMBER_NAMES = {"(999) 637-3009": "Mom", "(999) 637-5007": "Dad", "(999) 637-3003": "Sister"}
```

**Important formatting rules:**
- Must be valid JSON format with double quotes
- Phone numbers must match exactly as they appear in the PDF (including spaces and parentheses)
- Keep everything on a single line
- No trailing commas in the JSON object

**Without this file:** Output displays phone numbers
**With this file:** Output displays the mapped names

### Cost Allocation Strategies

**Equal Split (plan_cost_for_all_members: True)**
- Total plan cost ÷ all members = equal per-person cost
- Fairest for families where everyone uses similar features
- Example: $200 plan ÷ 10 members = $20/person base cost

**Tiered Split (plan_cost_for_all_members: False)**
- "Included" members share base plan cost
- Members with individual plans pay their own rate
- Better when some members have different plan tiers

Each member's final total = their share of plan cost + equipment + services + one-time charges

## Project Structure

```
.
├── main.py                  # Entry point - handles CLI and output formatting
├── analyze_bill_text.py     # PDF parser and data processor
├── configs.yml              # Configuration settings
├── requirements.txt         # Python dependencies
├── .env                     # Optional: Phone number to name mappings (create from .env.example)
├── .env.example             # Template for .env file
└── example_bill_summary/    # Sample PDF for testing
```

### Core Components

- **main.py**: Entry point that validates arguments, calls the parser, and formats output
- **analyze_bill_text.py**: PDF text extraction, table parsing, cost allocation logic
- **configs.yml**: Family plan configuration (member count, cost strategy)
- **.env**: Optional name mappings (copy from .env.example and customize)
- **requirements.txt**: Python dependencies (pandas, numpy, pypdf, pyyaml, tabulate, python-dotenv)

## Dependencies

All dependencies are iOS a-Shell compatible (pure Python, no C compilation):

- **pandas**: Data processing and calculations
- **numpy**: Numerical operations
- **pypdf**: Pure Python PDF text extraction (no C dependencies)
- **pyyaml**: Configuration file parsing
- **tabulate**: Table formatting for output
- **python-dotenv**: Environment variable loading for name mappings

Install via: `pip install -r requirements.txt`

## Troubleshooting

### "No module named 'pypdf'"
Install pypdf: `pip install pypdf`

### "Expected X rows but got Y"
Your `family_count` in `configs.yml` doesn't match the PDF. Check the bill and update the config to match the actual number of lines on your bill.

### "PDF file not found"
Verify the file path. In a-Shell, use `ls` to check file location. Paths are case-sensitive.

### Shortcut not capturing output
Make sure your Shortcut action is set to "Get output" or "Get result" after running the shell script.

### Wrong totals or missing members
- Verify `page_number` in config (usually 1)
- Check if T-Mobile changed their PDF format
- Open an issue with your PDF structure

### Names not showing up (still see phone numbers)
- Check that your `.env` file exists in the project root directory
- Verify the phone number format matches exactly (including spaces and parentheses)
- Ensure the JSON in `.env` is valid (use a JSON validator)
- Example: `(999) 637-3009` not `999-637-3009` or `(999)637-3009`

## iOS Shortcuts Tips

- **Testing**: Run the script manually in a-Shell first to verify it works
- **File Paths**: a-Shell stores files in `~/Documents/`; use absolute paths
- **Error Handling**: Add a "Show Alert" action to catch errors in your Shortcut
- **Automation**: Create a Personal Automation to process bills automatically when saved to a specific folder
- **Sharing Results**: Add actions to copy to clipboard or send via Messages

## Why Local Processing?

- **Privacy**: No cloud services, no uploading bills to third parties
- **Speed**: Instant processing, no waiting for email checks or API calls
- **Simplicity**: No authentication, no server setup, no cron jobs
- **Offline**: Works without internet (after initial pip install)
- **Cost**: Completely free, no cloud hosting fees

## Contributing

Found a bug or have a feature request? Open an issue or submit a pull request!

## Credits

- [a-Shell](https://github.com/holzschu/a-shell) - iOS terminal emulator
- [pypdf](https://github.com/py-pdf/pypdf) - Pure Python PDF library (no C dependencies)
- [pandas](https://pandas.pydata.org/) - Data analysis tools

## License

MIT License - feel free to use and modify for your own family bills!
