from django import forms
from sc_app.models import Closed

class YearSelect(forms.Form):
    year = forms.ChoiceField(choices=((2018,'2018'),(2019,'2019')), label="Select a year")


class CloseStore(forms.Form):

    year = forms.ChoiceField(choices=((2018,'2018'),(2019,'2019')), label="Select a year: ")
    store = forms.ModelChoiceField(Closed.objects.order_by('name'), empty_label='',to_field_name='name', label='Select a Store: ')
    type = forms.ChoiceField(choices=(("foot",'Foot Traffic'),('cbg','Census Blocks')), label="Select Data: ")
