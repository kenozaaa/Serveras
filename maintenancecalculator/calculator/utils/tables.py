import pandas as pd
from io import BytesIO

def calculate_totals_by_country(results_df):
    # Group by country and sum numeric columns only
    numeric_columns = results_df.select_dtypes(include='number').columns
    country_totals = results_df.groupby('Publication Country')[numeric_columns].sum()
    country_totals.reset_index(inplace=True)
    country_totals.rename(columns={'Publication Country': 'Country'}, inplace=True)
    return country_totals

def calculate_totals_by_year(results_df):
    # Assuming year columns are named with digits only, like '2024', '2025', etc.
    year_columns = [col for col in results_df.columns if col.isdigit()]
    year_totals = pd.DataFrame(results_df[year_columns].sum(), columns=['Total Fees by Year'])
    year_totals.reset_index(inplace=True)
    year_totals.rename(columns={'index': 'Year'}, inplace=True)
    return year_totals

def append_overview_tables_to_excel(results_df, output_buffer):
    """
    Append the two summary tables (total fees by country and total fees by year) to the right of the main DataFrame.
    Parameters:
    - results_df (DataFrame): The DataFrame containing processed patent data and fees.
    - output_buffer (BytesIO): The in-memory buffer for writing the Excel file.
    
    Returns:
    - output_buffer (BytesIO): Updated buffer with the additional tables.
    """
    country_totals_df = calculate_totals_by_country(results_df)
    year_totals_df = calculate_totals_by_year(results_df)

    # Use openpyxl engine and append to the same buffer
    with pd.ExcelWriter(output_buffer, engine='openpyxl', mode='a') as writer:
        # Write totals by country and year to the Excel sheet
        start_col = results_df.shape[1] + 2  # Leave a gap of 1 column
        country_totals_df.to_excel(writer, index=False, sheet_name='Fees Data', startcol=start_col)
        year_totals_df.to_excel(writer, index=False, sheet_name='Fees Data', startcol=start_col + country_totals_df.shape[1] + 2)

    output_buffer.seek(0)  # Rewind the buffer for further use
    return output_buffer