# 🌻 Daily With Doc - Youngevity Strategy Tool

A powerful web-based strategic analysis tool developed for Daily With Doc's Youngevity organizations, providing rank optimization and strategic move recommendations with professional branding and AI-powered insights.

## 🎯 Features

- **Organization Analysis**: Complete team structure and rank distribution
- **Strategic Recommendations**: PQV gap solutions, leg development opportunities, and placement strategies
- **60-Day Compliance**: Automatic enforcement of YGY's 60-day PCUST movement window
- **Order-Specific Suggestions**: Precise volume movement recommendations with order numbers
- **Interactive Dashboard**: User-friendly web interface with file upload and export capabilities
- **AI Strategic Advisor**: Get personalized strategic advice using your own API key from leading AI providers

## 🚀 Quick Start

### Local Development
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Run the Streamlit app:
   ```bash
   streamlit run streamlit_app.py
   ```

3. Open your browser and navigate to the provided URL (typically `http://localhost:8501`)

### Streamlit Cloud Deployment
1. Push this repository to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your GitHub repository
4. Deploy with these settings:
   - **Main file path**: `streamlit_app.py`
   - **Python version**: 3.9+

## 📁 Required Files

Upload these CSV files from your YGY back office:

1. **Group Volume Details CSV** - Contains order-level volume data
2. **Advanced Genealogy Report CSV** - Contains organizational structure and member data

## 🎯 Strategic Analysis Features

### Phase 1: Data Processing
- Dual CSV integration and validation
- Team data dictionary creation
- Downline tree construction

### Phase 2: Rank Calculations
- Accurate Paid-As Rank calculations using YGY compensation plan
- PQV, GQV-3CL, and leg requirement analysis
- Performance metrics and gaps identification

### Phase 3: Strategic Move Identification
- **Volume Donors**: Identify movable orders from PCUSTs older than 60 days
- **Placeable Assets**: Find PCUSTs within 60-day movement window
- **PQV Solutions**: Specific order combinations to close rank gaps
- **Leg Development**: Opportunities to advance underperforming legs
- **Strategic Placement**: Optimal locations for new PCUST placement

## 📊 Business Rules Compliance

- ✅ 60-day PCUST movement window enforcement
- ✅ Volume donor vs placeable asset categorization
- ✅ Autoship order exclusion from movement calculations
- ✅ Enroller organization restrictions for PCUST movement
- ✅ Expired distributor handling (sources vs targets)

## 🏆 YGY Rank Structure

1. **PCUST** (Preferred Customer) - 0 PQV
2. **ASC** (Associate) - 50 PQV
3. **BRA** (Brand Associate) - 100 PQV
4. **SA** (Sales Associate) - 150 PQV + 3 ASC+ legs
5. **SRA** (Senior Associate) - 200 PQV + 1,000 GQV-3CL + 3 BRA+ legs
6. **1SE** (1 Star Executive) - 250 PQV + 5,400 GQV-3CL + 3 SA+ legs
7. **2SE** (2 Star Executive) - 300 PQV + 7,500 GQV-3CL + 3 1SE+ legs
8. **3SE** (3 Star Executive) - 300 PQV + 10,500 GQV-3CL + 5 1SE+ legs
9. **4SE** (4 Star Executive) - 300 PQV + 27,000 GQV-3CL + 6 1SE+ legs
10. **5SE** (5 Star Executive) - 300 PQV + 43,200 GQV-3CL + 9 1SE+ legs
11. **EA** (Emerald Ambassador) - 300 PQV + 75,000 GQV-3CL + 12 1SE+ legs
12. **RA** (Ruby Ambassador) - 300 PQV + 150,000 GQV-3CL + 15 1SE+ legs
13. **DA** (Diamond Ambassador) - 300 PQV + 300,000 GQV-3CL + 18 1SE+ legs
14. **BDA** (Black Diamond Ambassador) - 300 PQV + 600,000 GQV-3CL + 21 1SE+ legs

## 📈 Export Features

- Strategic analysis reports in text format
- Downloadable recommendations with specific action items
- Complete analysis timestamp and leader information

## 🤖 AI Strategic Advisor

### Overview
The AI Strategic Advisor allows you to get personalized strategic advice using your own API key from leading AI providers. After your data analysis is complete, you can interact with an AI assistant that understands your organizational structure and YGY business rules.

### Supported AI Providers
- **OpenAI** (GPT-4) - Requires OpenAI API key
- **Anthropic** (Claude) - Requires Anthropic API key  
- **Google** (Gemini) - Requires Google AI API key

### Features
- **Organizational Strategy**: Get high-level growth recommendations
- **Level 0 Focus**: Specific advice for your organizational head
- **Rank Advancement**: Identify best advancement opportunities
- **Member-Specific Advice**: Targeted strategies for individual members
- **Interactive Chat**: Ask custom questions about your organization
- **Advice History**: Review previous AI recommendations

### Setup Instructions
1. Complete your data analysis (upload CSV files)
2. Obtain an API key from one of the supported providers:
   - **OpenAI**: <https://platform.openai.com/api-keys>
   - **Anthropic**: <https://console.anthropic.com/>
   - **Google AI**: <https://makersuite.google.com/app/apikey>
3. In the "Configure AI Advisor" section, select your provider and enter your API key
4. Click "Connect AI Advisor" - your key is only used for this session and never stored

### Privacy & Security
- ✅ API keys are never stored or logged
- ✅ Only used for the current browser session
- ✅ Your organizational data stays private (only shared with your chosen AI provider)
- ✅ All communication is encrypted via HTTPS

### Example Questions
- "What are the top 3 priorities for growing my organization?"
- "How can my Level 0 member maximize team growth?"
- "Which distributors should I focus on for rank advancement?"
- "What placement strategies should I consider?"
- "How can I improve my team's retention rate?"

## 🔧 Technical Stack

- **Python 3.9+**
- **Streamlit** - Web framework
- **Pandas** - Data processing
- **PyTZ** - Timezone handling
- **NumPy** - Numerical calculations

## 🛠️ Development

The application consists of:
- `ygy_data_setup.py` - Core business logic and analysis functions
- `streamlit_app.py` - Web interface and user interaction
- `requirements.txt` - Python dependencies
- `README.md` - Documentation

## 📞 Support

For technical support or business rule questions, please refer to your YGY compliance documentation and back office resources.
