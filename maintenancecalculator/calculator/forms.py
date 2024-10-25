from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

class UploadFileForm(forms.Form):
    file = forms.FileField(label='Select an Excel file')
    

class GPTForm(forms.Form):
    file = forms.FileField(label='Upload Excel File')
    prompt = forms.CharField(widget=forms.Textarea, label='Enter GPT Prompt')
    
    MODEL_CHOICES = [
        ('gpt-4o-mini', 'GPT-4o-Mini'),
        ('gpt-3.5-turbo-0125', 'GPT-3.5-Turbo'),
    ]
    model = forms.ChoiceField(choices=MODEL_CHOICES, label='Select Model')

    COLUMNS_CHOICES = [
        ('First Claim', 'First Claim'),
        ('Title', 'Title'),
        ('Abstract', 'Abstract'),
    ]
    columns = forms.MultipleChoiceField(choices=COLUMNS_CHOICES, widget=forms.CheckboxSelectMultiple, required=True)

    PREFIX_CHOICES = [
        ('TIPA', 'TIPA'),
        ('TIPX', 'TIPX')
    ]
    prefix = forms.ChoiceField(choices=PREFIX_CHOICES, label='Select Prefix')