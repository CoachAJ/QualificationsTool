# Youngevity Strategy Tool - Deployment Guide

## 🚀 Production Deployment

### Prerequisites
- Python 3.8 or higher
- Git for version control
- Streamlit Cloud account (or alternative hosting platform)

### Local Setup

1. **Clone the Repository**
   ```bash
   git clone https://github.com/CoachAJ/QualificationsTool.git
   cd QualificationsTool
   ```

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run Locally**
   ```bash
   streamlit run streamlit_app.py
   ```

### Cloud Deployment Options

#### Option 1: Streamlit Cloud (Recommended)
1. Push code to GitHub repository
2. Connect Streamlit Cloud to your GitHub account
3. Deploy directly from the repository
4. Streamlit Cloud will automatically install dependencies from `requirements.txt`

#### Option 2: Heroku
1. Create `Procfile`:
   ```
   web: streamlit run streamlit_app.py --server.port=$PORT --server.address=0.0.0.0
   ```
2. Deploy using Heroku CLI or GitHub integration

#### Option 3: AWS/GCP/Azure
- Use container deployment with Docker
- Configure environment variables for production

### Environment Configuration

#### Required Files
- `requirements.txt` - Python dependencies
- `streamlit_app.py` - Main application file
- `ygy_data_setup.py` - Business logic module
- `.streamlit/config.toml` - Streamlit configuration (optional)

#### Optional Configuration
Create `.streamlit/config.toml` for custom settings:
```toml
[theme]
primaryColor = "#1f77b4"
backgroundColor = "#ffffff"
secondaryBackgroundColor = "#f0f2f6"
textColor = "#262730"

[server]
maxUploadSize = 200
```

### Data Upload Requirements

#### CSV File Format
Your genealogy file must contain these columns:
- `ID#` - Member ID (required)
- `Name` - Member name (required)
- `Title` - PCUST or DISTRIBUTOR (required)
- `Rank` - Current rank (required)
- `Join Date` - Enrollment date in MM/DD/YYYY format (required)
- `Sponsor ID` - Sponsor's member ID (required)
- `Enroller` - Enroller's member ID
- `QV` - Personal volume
- `Level` - Hierarchical level
- `RepStatus` - Representative status

#### Volume File Format
Your volume file should contain:
- `Associate #` - Member ID
- `Order #` - Order identifier
- `Volume` - Order volume
- `Order Date` - Order date
- `Autoship` - Y/N flag

### Security Considerations

#### Data Privacy
- All data processing happens locally in the browser
- No data is stored on servers permanently
- Session data is cleared when browser closes
- Use HTTPS in production

#### File Upload Security
- File size limits enforced (200MB default)
- Only CSV files accepted
- Data validation performed on upload
- Invalid data flagged before processing

### Business Rule Compliance

#### PCUST 60-Day Rule
- Automatically enforced in all calculations
- PCUSTs within 60 days = MOVABLE
- PCUSTs past 60 days = LOCKED (volume donors only)
- Clear messaging in UI about move eligibility

#### Rank Advancement Rules
- PCUSTs cannot advance to distributor ranks
- Title field determines advancement eligibility
- Volume alone doesn't guarantee advancement
- Business rule violations flagged in validation

### Performance Optimization

#### Large Dataset Handling
- Optimized for organizations up to 10,000 members
- Hierarchical calculations use efficient algorithms
- Data validation runs in background
- Progress indicators for long operations

#### Memory Management
- Session state management for data persistence
- Efficient DataFrame operations
- Memory cleanup on file upload

### Troubleshooting

#### Common Issues
1. **Unicode Errors**: All emojis replaced with ASCII equivalents
2. **Date Format Issues**: Multiple date formats supported automatically
3. **Missing Columns**: Clear error messages guide data preparation
4. **Business Rule Violations**: Automatically detected and reported

#### Error Messages
- `[ALERT]` - Critical errors requiring attention
- `[WARNING]` - Data quality issues that may affect results
- `[OK]` - Successful operations
- `[INFO]` - Informational messages

### Monitoring and Maintenance

#### Health Checks
- Test with sample data monthly
- Verify business rule compliance
- Check for new Youngevity policy updates
- Monitor user feedback

#### Updates
- Business logic updates go in `ygy_data_setup.py`
- UI improvements go in `streamlit_app.py`
- Test all changes with `test_business_logic.py`
- Version control all changes

### Support Information

#### Business Logic Questions
- Review Youngevity compensation plan documentation
- Consult with YGY compliance team for rule clarifications
- Test edge cases thoroughly before deployment

#### Technical Support
- Check Streamlit documentation for UI issues
- Review pandas documentation for data processing
- Test locally before deploying changes

### Compliance Certification

✅ **60-Day PCUST Move Rule** - Fully implemented and tested
✅ **PCUST Rank Lock** - PCUSTs cannot advance to distributor ranks
✅ **Data Validation** - Business rule violations detected
✅ **Unicode Compatibility** - Windows console compatible
✅ **Error Handling** - Comprehensive error reporting
✅ **Testing Suite** - All business logic tested

This tool is ready for production use with full Youngevity business rule compliance.
