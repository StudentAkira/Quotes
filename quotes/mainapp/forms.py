from django import forms


class Quotes(forms.Form):

    quote = forms.BooleanField(required=False)

    def __init__(self, label):
        super().__init__()
        self.fields['quote'].label = label
