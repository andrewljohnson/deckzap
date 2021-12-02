from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

class SignUpForm(UserCreationForm):
    email = forms.EmailField(max_length=254, required=False, help_text='Optional. Add this if you want to be on the mailing list.')

    class Meta:
        model = User
        fields = ('username', 'password1', 'email' )

    def __init__(self, *args, **kwargs):
        super(SignUpForm, self).__init__(*args, **kwargs)
        del self.fields['password2']
        self.fields['email'].label = 'Email - Optional. Add this if you want to be on the mailing list.'
