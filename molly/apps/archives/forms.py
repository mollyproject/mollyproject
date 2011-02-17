from django import forms

class SearchForm(forms.Form):
    index = forms.ChoiceField(required=True,
                              label="Index",
                              choices=[('cql.anywhere', 'Keywords'),
                                       ('dc.title', 'Titles'),
                                       ('dc.creator', 'Creators'),
                                       ('dc.subject', 'Subjects'),
                                       ('bath.name', 'Names')
                              ]
    )
    relation = forms.CharField(required=True,
                               label="Relation",
                               initial="all/rel.algorithm=okapi",
                               widget=forms.HiddenInput
    )
    value = forms.CharField(required=True,
                            label="Value",
                            initial=""
    )


class BrowseForm(forms.Form):
    index = forms.ChoiceField(required=True,
                              label="Index",
                              choices=[('dc.title', 'Titles'),
                                       ('dc.creator', 'Creators'),
                                       ('dc.subject', 'Subjects'),
                                       ('bath.name', 'Names')
                              ]
    )
    relation = forms.CharField(required=True,
                               label="Relation",
                               initial="exact",
                               widget=forms.HiddenInput
    )
    value = forms.CharField(required=True,
                            label="Value",
                            initial=""
    )

