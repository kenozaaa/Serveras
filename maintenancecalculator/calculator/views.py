from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, Http404
from django.conf import settings
from .forms import UploadFileForm, GPTForm
from .models import CalculationResult, GptResult
from io import BytesIO
import zipfile
import pandas as pd
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import redirect
import logging 
import os
from .utils.calculation import (
    calculate_fees_issued_date, calculate_fees_filing_date, post_process_fees, date_check
)
from .utils.excel_utils import read_patent_data, extract_patent_info
from .utils.fees_reader import read_fees_data
from .utils.total import add_total_fees_per_patent, calculate_grand_total

from .utils.locate import locate_country_code_in_fees
from .utils.gpt_utils.operations import clean_and_extract_relevant_columns, categorize_claims, save_to_excel
from .utils.exceptions import MissingRequiredColumnsError, InvalidCountryCodeError, ExcelFileReadError, ExcelError
from .utils.gpt_utils.exceptions import GPTInvalidColumnsError

from openpyxl import load_workbook
from .utils.overview import create_overview_sheet, format_dates_and_currency
###################################### LOGIN/LOGOUT #########################################

# Login view
def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, 'Invalid username or password.')
    return render(request, 'calculator/login.html')

# Logout view
def logout_view(request):
    logout(request)
    return redirect('login')  # Redirect to login page after logout

def login_redirect_view(request):
    if request.user.is_authenticated:
        return redirect('home')
    return redirect('login')

############################################ HOME ############################################
@login_required
def home(request):
    return render(request, 'calculator/home.html', context={'user': request.user})


############################################ FEES VIEW ############################################

def view_fees_dollars(request):
    file_path = os.path.join(settings.BASE_DIR, 'calculator', 'data', 'feesdollars.xlsx')
    fees_info = read_fees_data(file_path)  # Use the updated read_fees_data function

    if fees_info.empty:
        logging.warning("Fees data is empty or not available")

    data = fees_info.to_html(classes='table table-striped', index=False)
    return render(request, 'calculator/feesdollars.html', {'data': data})

def download_fees(request):
    file_path = os.path.join(settings.BASE_DIR, 'calculator', 'data', 'feesdollars.xlsx')
    with open(file_path, 'rb') as file:
        response = HttpResponse(file.read(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = 'attachment; filename="FeesDollars.xlsx"'
        return response

def upload_fees(request):
    if request.method == 'POST' and request.FILES.get('fees_file'):
        file = request.FILES['fees_file']
        file_path = os.path.join(settings.BASE_DIR, 'calculator', 'data', 'feesdollars.xlsx')
        with open(file_path, 'wb+') as destination:
            for chunk in file.chunks():
                destination.write(chunk)
        return redirect('view_fees_dollars')
    return Http404("Invalid request")

############################################ CALCULATION VIEW ############################################

@login_required
def calculate_fees_view(request):
    if request.method == "POST":
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            file = form.cleaned_data["file"]
            try:
                # Read patent data and validate columns
                full_patent_df, patent_df = read_patent_data(file)
                patent_info = extract_patent_info(patent_df)
                
                # Read fees data
                fees_info_path = os.path.join(settings.BASE_DIR, 'calculator', 'data', 'feesdollars.xlsx')
                fees_info = read_fees_data(fees_info_path)

                # Extract country codes and names (second row for names)
                country_codes_and_names = {
                    code: {
                        'country': fees_info.iloc[1][code],
                        'type': fees_info.iloc[0][code]
                    }
                    for code in fees_info.columns
                }

                # Locate country code in fees and calculate fees
                date_types = locate_country_code_in_fees(patent_info, fees_info)

                # Prepare results DataFrame
                results_df = patent_df.copy()
                results_df['Date Type'] = None

                for i, patent in enumerate(patent_info):
                    results_df = date_check(patent, date_types, fees_info, results_df, i)

                # Step 1: Ensure the relevant columns (Total Fees, Year Columns) are numeric
                if 'Total Fees' in results_df.columns:
                    results_df['Total Fees'] = pd.to_numeric(results_df['Total Fees'], errors='coerce')

                # Identify year columns and ensure they are numeric
                year_columns = [col for col in results_df.columns if col.isdigit()]
                if year_columns:
                    results_df[year_columns] = results_df[year_columns].apply(pd.to_numeric, errors='coerce')

                # Step 2: Post-process the fees
                results_df = post_process_fees(results_df)
                results_df = add_total_fees_per_patent(results_df)
                results_df = calculate_grand_total(results_df)

                # Step 3: Save to BytesIO
                output_buffer = BytesIO()

                # Write the calculated fees to BytesIO
                with pd.ExcelWriter(output_buffer, engine='openpyxl') as writer:
                    results_df.to_excel(writer, sheet_name='Calculated Fees', index=False)

                # Step 4: Load the workbook from BytesIO using openpyxl
                output_buffer.seek(0)  # Reset buffer pointer
                workbook = load_workbook(output_buffer)  # Load the workbook into openpyxl

                # Step 5: Create the overview sheet
                create_overview_sheet(workbook, results_df)

                # Step 6: Apply formatting to dates and currency
                format_dates_and_currency(workbook)

                # Step 7: Save the final workbook back to BytesIO
                final_output = BytesIO()
                workbook.save(final_output)  # Save the updated workbook to BytesIO
                final_output.seek(0)  # Reset pointer to the beginning

                # Generate new filenames and project ID
                project_id = CalculationResult.objects.count() + 1
                original_filename = os.path.splitext(file.name)[0]
                new_filename = f"TIPA_MC_{project_id}_{original_filename}.xlsx"

                # Step 8: Save the binary content and metadata to PostgreSQL
                CalculationResult.objects.create(
                    filename=new_filename,
                    file_content=final_output.getvalue(),  # Save the Excel file content as binary
                    created_by=request.user
                )

                # Redirect after successful processing
                return redirect('calculate_fees')

            except (MissingRequiredColumnsError, ExcelError) as e:
                error_message = str(e)
            except Exception as e:
                error_message = f"An unexpected error occurred: {str(e)}"
        
        # If there's an error, fetch the stored files and return the error message
        result_files_calculation = CalculationResult.objects.order_by('-created_at')
        return render(request, 'calculator/calculate.html', {
            'form': form,
            'error_message': error_message,
            'result_files_calculation': result_files_calculation,
            'country_codes_and_names': country_codes_and_names,  # Pass the country codes and names
        })
    
    else:
        form = UploadFileForm()

        # Read fees data to get country codes and names
        fees_info_path = os.path.join(settings.BASE_DIR, 'calculator', 'data', 'feesdollars.xlsx')
        fees_info = read_fees_data(fees_info_path)

        # Extract country codes and names (second row for names)
        country_codes_and_names = {
            code: {
                'country': fees_info.iloc[1][code],
                        'type': fees_info.iloc[0][code]
                    }
                    for code in fees_info.columns
                }

        # Normal display when there's no error
        result_files_calculation = CalculationResult.objects.order_by('-created_at')
        return render(request, 'calculator/calculate.html', {
            'form': form,
            'result_files_calculation': result_files_calculation,
            'country_codes_and_names': country_codes_and_names,  # Pass the country codes and names
        })

############################################ FILE DOWNLOAD ############################################

def bulk_download(request):
    if request.method == "POST":
        selected_files = request.POST.getlist('selected_files')  # Get list of selected files

        if not selected_files:
            raise Http404("No files selected for download.")

        # Attempt to fetch selected CalculationResult or GptResult files
        result_files_calculation = CalculationResult.objects.filter(filename__in=selected_files)
        result_files_gpt = GptResult.objects.filter(filename__in=selected_files)

        # Combine both CalculationResult and GptResult files
        result_files = list(result_files_calculation) + list(result_files_gpt)

        if not result_files:
            raise Http404("No files found for the selected filenames.")

        if len(result_files) == 1:
            # If only one file is selected, return it directly as an Excel file
            result_file = result_files[0]
            response = HttpResponse(result_file.file_content, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
            response['Content-Disposition'] = f'attachment; filename="{result_file.filename}"'
            return response

        else:
            # If multiple files are selected, create a ZIP archive
            zip_buffer = BytesIO()
            with zipfile.ZipFile(zip_buffer, 'w') as zip_file:
                for result_file in result_files:
                    zip_file.writestr(result_file.filename, result_file.file_content)
            zip_buffer.seek(0)  # Reset the buffer's position to the beginning

            response = HttpResponse(zip_buffer, content_type='application/zip')
            response['Content-Disposition'] = 'attachment; filename="selected_files.zip"'
            return response

    raise Http404("Invalid request method.")
############################################  GPT VIEWS ############################################

@login_required
def gpt_categorize_view(request):
    if request.method == 'POST':
        form = GPTForm(request.POST, request.FILES)
        if form.is_valid():
            file = form.cleaned_data['file']
            prompt = form.cleaned_data['prompt']
            model = form.cleaned_data['model']
            prefix = request.POST.get('prefix', 'TIPA')  # Default to TIPA if not selected

            # Get the user-selected columns
            selected_columns = request.POST.getlist('columns')

            try:
                # Process the file and categorize it using GPT
                df = clean_and_extract_relevant_columns(file, selected_columns)
                categorized_df = categorize_claims(df, model, prompt, selected_columns)

                # Save the result into the database with proper naming
                project_id = GptResult.objects.count() + 1
                original_filename = os.path.splitext(file.name)[0]
                new_filename = f"{prefix}_GPT_{project_id}_{original_filename}.xlsx"  # Apply the selected prefix to the filename

                # Save the categorized data to an Excel file
                output_buffer = BytesIO()
                save_to_excel(categorized_df, output_buffer)
                output_buffer.seek(0)

                # Save in the database
                GptResult.objects.create(
                    filename=new_filename,  # Save with the new filename including the prefix
                    file_content=output_buffer.getvalue(),
                    prompt=prompt,
                    model_used=model,
                    prefix=prefix,  # Save the selected prefix (TIPA/TIPX)
                    created_by=request.user
                )

                return redirect('gpt-categorize')

            except Exception as e:
                error_message = f"Failed to process the Excel file: {str(e)}"
                result_files_gpt = GptResult.objects.order_by('-created_at')
                return render(request, 'calculator/gpt.html', {
                    'form': form,
                    'error_message': error_message,
                    'result_files_gpt': result_files_gpt
                })
    
    else:
        form = GPTForm()

    # Normal display when there's no error
    result_files_gpt = GptResult.objects.order_by('-created_at')
    return render(request, 'calculator/gpt.html', {
        'form': form,
        'result_files_gpt': result_files_gpt
    })

############################################  login/logout VIEWS ############################################



