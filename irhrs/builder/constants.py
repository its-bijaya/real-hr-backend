FIELDS_FILTER_CHOICES = (
    ('exact', 'Equals'),
    ('iexact', 'Equals (case-insensitive)'),
    ('contains', 'Contains'),
    ('icontains', 'Contains (case-insensitive)'),
    ('in', 'in (comma separated 1,2,3)'),
    ('gt', 'Greater than'),
    ('gte', 'Greater than equals'),
    ('lt', 'Less than'),
    ('lte', 'Less than equals'),
    ('startswith', 'Starts with'),
    ('istartswith', 'Starts with (case-insensitive)'),
    ('endswith', 'Ends with'),
    ('iendswith', 'Ends with  (case-insensitive)'),
    ('range', 'range'),
    ('isnull', 'Is null'),
)

FIELDS_ORDERING_CHOICES = (
    ('Asc', 'Ascending'),
    ('Desc', 'Descending')
)

FIELDS_AGGREGATE_CHOICES = (
    ('Sum', 'Sum'),
    ('Count', 'Count'),
    ('Avg', 'Avg'),
    ('Max', 'Max'),
    ('Min', 'Min'),
)
