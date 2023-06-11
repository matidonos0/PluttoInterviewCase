def riskyfier(df):
    if df['Tiene B. concursal'] != 0:
        return 'high_risk'
    elif df['Deuda Directa castigada'] != 0:
        return 'high_risk'
    elif df['Causas legales en contra'] != 0:
        return 'medium_risk'
    elif df['Tiene B. comercial'] + df['Tiene B. laboral'] != 0:
        return 'medium_risk'
    elif df['Deuda Directa morosa'] + df['Deuda Leasing morosa'] != 0:
        return 'medium_risk'
    else:
        return 'low_risk'
  