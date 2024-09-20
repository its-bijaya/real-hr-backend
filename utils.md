### core/utils

* `get_attribute_from_validated_data_or_instance`

```
Gets attr from validated_data or self.instance if partial.
Use this method for obtaining attribute instead of
`validated_data.get(attr)`
:param attribute: name of the attribute e.g. `pk`
:param validated_data: dict of validated_data
:param serializer: serializer instance i.e. `self`
:return: attribute from validated_data or self.instance if the method is
`PATCH`. Does not care about instance if `PUT`.
```

```python
    first_name = get_attribute_from_validated_data_or_instance(
        'first_name',
        validated_data,
        self
    )
```
