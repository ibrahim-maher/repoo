# system/analytics/analytics_tools.py
import pandas as pd

def analyze_registration_data(registrations):
    df = pd.DataFrame(list(registrations.values()))
    analysis = df.describe()
    return analysis