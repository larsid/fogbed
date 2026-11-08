import fogbed


def test_fail_api_is_exported_from_package_root():
    for name in [
        'FailController',
        'CrashFail',
        'DisconnectFail',
        'AvailabilityFail',
        'AvailabilityMode',
        'SplitMethod',
        'SelectionMethod'
    ]:
        assert hasattr(fogbed, name)
