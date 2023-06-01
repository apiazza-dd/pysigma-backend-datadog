# pylint: disable=too-many-lines
import pytest
from sigma.collection import SigmaCollection

# TODO: Remove once backend is published in pySigma
import sys

sys.path.append(".")
# from sigma.backends.datadog import DatadogBackend

from dd_sigma.backends.datadog import DatadogBackend


@pytest.mark.smoke
def test_always_passes():
    assert True


@pytest.fixture
def datadog_backend():
    return DatadogBackend()


## Query Conversions
def test_datadog_and_expression(datadog_backend: DatadogBackend):
    assert (
        datadog_backend.convert(
            SigmaCollection.from_yaml(
                """
            title: Test
            status: test
            logsource:
                service: cloudtrail
                product: aws
            detection:
                sel:
                    fieldA: valueA
                    fieldB: valueB
                condition: sel
        """
            )
        )
        == ["@fieldA:valueA AND @fieldB:valueB"]
    )


def test_datadog_or_expression(datadog_backend: DatadogBackend):
    assert (
        datadog_backend.convert(
            SigmaCollection.from_yaml(
                """
            title: Test
            status: test
            logsource:
                service: cloudtrail
                product: aws
            detection:
                sel1:
                    fieldA: valueA
                sel2:
                    fieldB: valueB
                condition: 1 of sel*
        """
            )
        )
        == ["@fieldA:valueA OR @fieldB:valueB"]
    )


def test_datadog_and_or_expression(datadog_backend: DatadogBackend):
    assert (
        datadog_backend.convert(
            SigmaCollection.from_yaml(
                """
            title: Test
            status: test
            logsource:
                service: cloudtrail
                product: aws
            detection:
                sel:
                    fieldA:
                        - valueA1
                        - valueA2
                    fieldB:
                        - valueB1
                        - valueB2
                condition: sel
        """
            )
        )
        == [
            "(@fieldA:valueA1 OR @fieldA:valueA2) AND (@fieldB:valueB1 OR @fieldB:valueB2)"
        ]
    )


def test_datadog_complex_expressions(datadog_backend: DatadogBackend):
    assert (
        datadog_backend.convert(
            SigmaCollection.from_yaml(
                """
            title: Test
            status: test
            logsource:
                service: cloudtrail
                product: aws
            detection:
                sel1:
                    fieldA: valueA1
                    fieldB: valueB1
                sel2:
                    fieldA: valueA2
                    fieldB: valueB2
                condition: 1 of sel*
        """
            )
        )
        == [
            "@fieldA:valueA1 AND @fieldB:valueB1 OR @fieldA:valueA2 AND @fieldB:valueB2"  # We don't need using parenthesis in this statement due to the order of precedence NOT, AND, OR specified in our backend
        ]
    )


def test_datadog_filters(datadog_backend: DatadogBackend):
    assert (
        datadog_backend.convert(
            SigmaCollection.from_yaml(
                """
            title: Test
            status: test
            logsource:
                service: cloudtrail
                product: aws
            detection:
                selection:
                    - Product|contains: 'examplePhrase'
                filter:
                    Image|endswith: '\client32.exe'
                condition: selection and not filter
        """
            )
        )
        == ["@Product:*examplePhrase* AND NOT @Image:*\\client32.exe"]
    )


def test_datadog_wildcard_expression(datadog_backend: DatadogBackend):
    assert (
        datadog_backend.convert(
            SigmaCollection.from_yaml(
                """
            title: Test
            status: test
            logsource:
                service: cloudtrail
                product: aws
            detection:
                sel:
                    fieldA:
                        - valueA
                        - valueB
                        - valueC*
                condition: sel
        """
            )
        )
        == ["@fieldA:valueA OR @fieldA:valueB OR @fieldA:valueC*"]
    )


def test_datadog_cidr_query(datadog_backend: DatadogBackend):
    assert (
        datadog_backend.convert(
            SigmaCollection.from_yaml(
                """
            title: Cidr Test
            status: test
            logsource:
                service: cloudtrail
                product: aws
            detection:
                sel:
                    field|cidr: 192.168.0.0/16
                condition: sel
        """
            )
        )
        == ["@field:192.168.*"]
    )


def test_datadog_field_name_with_whitespace(datadog_backend: DatadogBackend):
    assert (
        datadog_backend.convert(
            SigmaCollection.from_yaml(
                """
            title: Blank Space Test
            status: test
            logsource:
                service: cloudtrail
                product: aws
            detection:
                sel:
                    field name: value
                condition: sel
        """
            )
        )
        == ["@field\\ name:value"]
    )  # double slash is escaping the escape


## Rule Conversions
def test_datadog_siem_rule_output(datadog_backend: DatadogBackend):
    """Test for NDJSON output with embedded query string query."""
    rule = SigmaCollection.from_yaml(
        """
            title: Test
            id: c277adc0-f0c4-42e1-af9d-fab062992156
            status: test
            logsource:
                service: cloudtrail
                product: aws
            detection:
                sel:
                    fieldA: valueA
                    fieldB: valueB
                condition: sel
        """
    )
    dd_rule_conversion_result = datadog_backend.convert(rule, output_format="siem_rule")
    assert dd_rule_conversion_result[0] == {
        "product": ["security_monitoring"],
        "name": "SIGMA Threshold Detection - Test",
        "message": "SIGMA Rule ID: c277adc0-f0c4-42e1-af9d-fab062992156 \n False Positives: []) \n Description: None",
        "tags": [],
        "source": "cloudtrail",
        "queries": [
            {
                "name": "",
                "query": "@fieldA:valueA AND @fieldB:valueB",
                "groupByFields": ["@userIdentity.arn"],
                "distinctFields": [],
                "aggregation": "",
            }
        ],
        "options": {
            "detectionMethod": "threshold",
            "evaluationWindow": 3600,
            "keepAlive": 3600,
            "maxSignalDuration": 86400,
        },
        "cases": [
            {"status": "low", "notifications": [], "name": "", "condition": "a > 0"}
        ],
    }


def test_datadog_siem_rule_output_with_tags(datadog_backend: DatadogBackend):
    """Test for NDJSON output with embedded query string query."""
    rule = SigmaCollection.from_yaml(
        """
            title: Test
            id: 0cb654e0-ff23-11ed-be56-0242ac120002
            status: test
            logsource:
                service: cloudtrail
                product: aws
            tags:
                - attack.t1548
                - attack.t1550
                - attack.t1550.001
            detection:
                sel:
                    fieldA: valueA
                    fieldB: valueB
                condition: sel
        """
    )
    dd_rule_conversion_result = datadog_backend.convert(rule, output_format="siem_rule")
    assert dd_rule_conversion_result[0] == {
        "product": ["security_monitoring"],
        "name": "SIGMA Threshold Detection - Test",
        "message": "SIGMA Rule ID: 0cb654e0-ff23-11ed-be56-0242ac120002 \n False Positives: []) \n Description: None",
        "tags": ["attack-t1548", "attack-t1550", "attack-t1550.001"],
        "source": "cloudtrail",
        "queries": [
            {
                "name": "",
                "query": "@fieldA:valueA AND @fieldB:valueB",
                "groupByFields": ["@userIdentity.arn"],
                "distinctFields": [],
                "aggregation": "",
            }
        ],
        "options": {
            "detectionMethod": "threshold",
            "evaluationWindow": 3600,
            "keepAlive": 3600,
            "maxSignalDuration": 86400,
        },
        "cases": [
            {"status": "low", "notifications": [], "name": "", "condition": "a > 0"}
        ],
    }


def test_datadog_rule_types(datadog_backend: DatadogBackend):
    """Test for NDJSON output with embedded query string query."""
    rule = SigmaCollection.from_yaml(
        """
            title: AWS Root Credentials
            id: 0cb654e0-ff23-11ed-be56-0242ac120002
            status: test
            description: Detects AWS root account usage
            references:
                - https://docs.aws.amazon.com/IAM/latest/UserGuide/id_root-user.html
            author: testauthor
            date: 2020/01/21
            modified: 2022/10/09
            tags:
                - attack.privilege_escalation
                - attack.t1078.004
            logsource:
                product: aws
                service: cloudtrail
            detection:
                selection_usertype:
                    userIdentity.type: Root
                selection_eventtype:
                    eventType: AwsServiceEvent
                condition: selection_usertype and not selection_eventtype
            falsepositives:
                - AWS Tasks That Require AWS Account Root User Credentials https://docs.aws.amazon.com/general/latest/gr/aws_tasks-that-require-root.html
            level: medium
        """
    )
    dd_rule_conversion_result = datadog_backend.convert(rule, output_format="siem_rule")
    assert dd_rule_conversion_result[0] == {
        "product": ["security_monitoring"],
        "name": "SIGMA Threshold Detection - AWS Root Credentials",
        "message": "SIGMA Rule ID: 0cb654e0-ff23-11ed-be56-0242ac120002 \n False Positives: ['AWS Tasks That Require AWS Account Root User Credentials https://docs.aws.amazon.com/general/latest/gr/aws_tasks-that-require-root.html']) \n Description: Detects AWS root account usage",
        "tags": ["attack-privilege_escalation", "attack-t1078.004"],
        "source": "cloudtrail",
        "queries": [
            {
                "name": "",
                "query": "@userIdentity.type:Root AND NOT @eventType:AwsServiceEvent",
                "groupByFields": ["@userIdentity.arn"],
                "distinctFields": [],
                "aggregation": "",
            }
        ],
        "options": {
            "detectionMethod": "threshold",
            "evaluationWindow": 3600,
            "keepAlive": 3600,
            "maxSignalDuration": 86400,
        },
        "cases": [
            {"status": "medium", "notifications": [], "name": "", "condition": "a > 0"}
        ],
    }


def test_datadog_rule_types_2(datadog_backend: DatadogBackend):
    """Test for NDJSON output with embedded query string query."""
    rule = SigmaCollection.from_yaml(
        """
            title: Possible DNS Rebinding
            id: ec5b8711-b550-4879-9660-568aaae2c3ea
            name: "Name"
            status: unsupported
            description: 'Detects DNS-answer with TTL <10.'
            date: 2023/05/25
            author: Author
            references:
                - https://github.com/sigmahq
            tags:
                - attack.command_and_control
                - attack.t1043
            falsepositives: 
                - test1
                - test2
            logsource:
                product: aws
                service: cloudtrail
            detection:
                selection:
                    answer: '*'
                filter1:
                    ttl: '>0'
                filter2:
                    ttl: '<10'
                timeframe: 30s
                condition: selection and filter1 and filter2 
            level: medium
        """
    )
    dd_rule_conversion_result = datadog_backend.convert(rule, output_format="siem_rule")
    assert dd_rule_conversion_result[0] == {
        "product": ["security_monitoring"],
        "name": "SIGMA Threshold Detection - Possible DNS Rebinding",
        "message": "SIGMA Rule ID: ec5b8711-b550-4879-9660-568aaae2c3ea \n False Positives: ['test1', 'test2']) \n Description: Detects DNS-answer with TTL <10.",
        "tags": ["attack-command_and_control", "attack-t1043"],
        "source": "cloudtrail",
        "queries": [
            {
                "name": "",
                "query": "@answer:* AND @ttl:\\>0 AND @ttl:\\<10",
                "groupByFields": ["@userIdentity.arn"],
                "distinctFields": [],
                "aggregation": "",
            }
        ],
        "options": {
            "detectionMethod": "threshold",
            "evaluationWindow": 3600,
            "keepAlive": 3600,
            "maxSignalDuration": 86400,
        },
        "cases": [
            {"status": "medium", "notifications": [], "name": "", "condition": "a > 0"}
        ],
    }
