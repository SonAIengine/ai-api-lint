from __future__ import annotations

from ai_api_lint.engine import RuleEngine


def create_default_engine() -> RuleEngine:
    """Create a RuleEngine with all default rules registered."""
    from ai_api_lint.rules.description import (
        AI010_DescriptionMissing,
        AI011_DescriptionTooShort,
        AI012_DescriptionRepeatsPath,
        AI013_DescriptionNoUsageHint,
        AI014_ParamDescriptionMissing,
        AI015_EnumNoDescription,
    )
    from ai_api_lint.rules.mcp_readiness import (
        AI060_PythonReservedWord,
        AI061_TooManyParams,
        AI062_TooManyOperations,
        AI063_InconsistentVerbPatterns,
        AI064_NoSecurityScheme,
    )
    from ai_api_lint.rules.operation_id import (
        AI001_OperationIdMissing,
        AI002_OperationIdFormat,
        AI003_OperationIdLength,
        AI004_OperationIdSpecialChars,
        AI005_OperationIdDuplicate,
    )
    from ai_api_lint.rules.parameters import (
        AI020_IdParamNoSourceHint,
        AI021_TooManyRequiredParams,
        AI022_ParamMissingType,
        AI023_ComplexParamNoExample,
    )
    from ai_api_lint.rules.path_design import (
        AI050_PathContainsVerb,
        AI051_PathTooDeep,
        AI052_InconsistentNaming,
        AI053_MissingTags,
    )
    from ai_api_lint.rules.request_body import (
        AI030_MutationNoRequestBody,
        AI031_RequestBodyNoProperties,
        AI032_RequestBodyNoRequired,
        AI033_RequestBodyNotJson,
        AI034_RequestBodyNoDescription,
    )
    from ai_api_lint.rules.response import (
        AI040_NoSuccessResponse,
        AI041_SuccessResponseNoSchema,
        AI042_NoClientErrorResponse,
        AI043_ErrorResponseNoDescription,
        AI044_GenericErrorOnly,
    )

    engine = RuleEngine()

    # Per-operation rules
    for rule_cls in [
        AI001_OperationIdMissing,
        AI002_OperationIdFormat,
        AI003_OperationIdLength,
        AI004_OperationIdSpecialChars,
        AI010_DescriptionMissing,
        AI011_DescriptionTooShort,
        AI012_DescriptionRepeatsPath,
        AI013_DescriptionNoUsageHint,
        AI014_ParamDescriptionMissing,
        AI015_EnumNoDescription,
        AI020_IdParamNoSourceHint,
        AI021_TooManyRequiredParams,
        AI022_ParamMissingType,
        AI023_ComplexParamNoExample,
        AI030_MutationNoRequestBody,
        AI031_RequestBodyNoProperties,
        AI032_RequestBodyNoRequired,
        AI033_RequestBodyNotJson,
        AI034_RequestBodyNoDescription,
        AI040_NoSuccessResponse,
        AI041_SuccessResponseNoSchema,
        AI042_NoClientErrorResponse,
        AI043_ErrorResponseNoDescription,
        AI044_GenericErrorOnly,
        AI050_PathContainsVerb,
        AI051_PathTooDeep,
        AI053_MissingTags,
        AI060_PythonReservedWord,
        AI061_TooManyParams,
    ]:
        engine.register(rule_cls())

    # Global rules (check whole spec, not individual operations)
    engine.register_global(AI005_OperationIdDuplicate().check_global)
    engine.register_global(AI052_InconsistentNaming().check_global)
    engine.register_global(AI062_TooManyOperations().check_global)
    engine.register_global(AI063_InconsistentVerbPatterns().check_global)
    engine.register_global(AI064_NoSecurityScheme().check_global)

    return engine
