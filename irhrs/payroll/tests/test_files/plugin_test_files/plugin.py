def init(calculator, package_heading):
    print('START_____________OUTPUT FROM TEST PLUGIN_____________')

    print(calculator.employee, package_heading, calculator.from_date, calculator.to_date)

    print('END_____________OUTPUT FROM TEST PLUGIN_____________')

    return 100, [
        dict(
            model_name="XYZ",
            instance_id=2,
            url=""
        )
    ]