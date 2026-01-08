=> What the project does

This is a development project in quantitative financial analysis.
It consists of two independent applications:

app_quant_a: single-asset analysis and risk/performance indicators

app_quant_b: multi-asset analysis and portfolio logic

A platform serves as a single entry point and allows either application to be easily launched from a centralized interface.

Each application operates autonomously, while being integrated into a common environment


=> The purpose

The project aims to structure quantitative tools in a modular way, separate responsibilities (single asset vs. portfolio), facilitate experimentation, comparison, and evolution of strategies and we centralize access to tools without creating strong dependencies between them

This approach is particularly well suited to deployment on a server (here in EC2)


=> Prerequisites 

Python 3.10+, a virtual environment is recommended and streamlit installed

To activate the virtual environment you need to write : source .venv/bin/activate

The following Python libraries are required (see requirements.txt):
- 'streamlit' for the web application framework
- 'pandas' for data manipulation
- 'numpy' for numerical computations
- 'yfinance' for financial data retrieving from Yahoo Finance
- 'requests' for HTTP requests handling
- 'matplotlib' for basic plotting utilities
- 'plotly' for interactive visualizations
- 'streamlit-autorefresh' for automatic dashboard refresh

To launch the platform you need to write : streamlit run platform.py --server.port 8500 (you should have this URL: http://51.21.180.222:8500)


=> Maintenance and contributions

Quant A : maintained by Chloé Loisel-Carbon
Quant B : maintained by Ambroise Megel
