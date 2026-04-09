from finance_data.provider.metadata.validator import validate_toolspec_registry_consistency


def test_toolspec_registry_consistency_passes():
    results = validate_toolspec_registry_consistency()
    failures = [str(result) for result in results if not result.passed]
    assert not failures, "\n".join(failures)
