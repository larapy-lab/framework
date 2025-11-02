import pytest
from datetime import datetime, timedelta
from larapy.validation.validator import Validator
from larapy.validation.rules import (
    ActiveUrlRule,
    AfterRule,
    AfterOrEqualRule,
    BeforeRule,
    BeforeOrEqualRule,
    DateEqualsRule,
    InArrayRule,
    BailRule
)


class TestActiveUrlRule:
    def test_active_url_with_valid_domain(self):
        rule = ActiveUrlRule()
        assert rule.passes('website', 'https://www.google.com', {})
        assert rule.passes('website', 'http://github.com', {})

    def test_active_url_with_invalid_domain(self):
        rule = ActiveUrlRule()
        assert not rule.passes('website', 'https://this-domain-does-not-exist-12345.com', {})

    def test_active_url_with_non_string(self):
        rule = ActiveUrlRule()
        assert not rule.passes('website', 123, {})
        assert not rule.passes('website', None, {})
        assert not rule.passes('website', [], {})

    def test_active_url_with_invalid_format(self):
        rule = ActiveUrlRule()
        assert not rule.passes('website', 'not-a-url', {})
        assert not rule.passes('website', '', {})

    def test_active_url_without_hostname(self):
        rule = ActiveUrlRule()
        assert not rule.passes('website', 'http://', {})

    def test_active_url_message(self):
        rule = ActiveUrlRule()
        assert "valid URL" in rule.message()


class TestAfterRule:
    def test_after_with_static_date(self):
        rule = AfterRule('2024-01-01')
        assert rule.passes('date', '2024-01-02', {})
        assert rule.passes('date', '2024-12-31', {})
        assert not rule.passes('date', '2023-12-31', {})
        assert not rule.passes('date', '2024-01-01', {})

    def test_after_with_datetime_value(self):
        rule = AfterRule('2024-01-01')
        date_obj = datetime(2024, 1, 2, 10, 30)
        assert rule.passes('date', date_obj, {})

    def test_after_with_field_reference(self):
        rule = AfterRule('start_date')
        data = {'start_date': '2024-01-01', 'end_date': '2024-01-02'}
        assert rule.passes('end_date', '2024-01-02', data)
        assert not rule.passes('end_date', '2023-12-31', data)

    def test_after_with_today_keyword(self):
        rule = AfterRule('today')
        tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        assert rule.passes('date', tomorrow, {})
        assert not rule.passes('date', yesterday, {})

    def test_after_with_tomorrow_keyword(self):
        rule = AfterRule('tomorrow')
        future = (datetime.now() + timedelta(days=2)).strftime('%Y-%m-%d')
        assert rule.passes('date', future, {})

    def test_after_with_yesterday_keyword(self):
        rule = AfterRule('yesterday')
        today = datetime.now().strftime('%Y-%m-%d')
        assert rule.passes('date', today, {})

    def test_after_with_datetime_field_reference(self):
        rule = AfterRule('start_date')
        data = {'start_date': datetime(2024, 1, 1), 'end_date': datetime(2024, 1, 2)}
        assert rule.passes('end_date', datetime(2024, 1, 2), data)

    def test_after_with_iso_format_z_suffix(self):
        rule = AfterRule('2024-01-01T00:00:00Z')
        assert rule.passes('date', '2024-01-02T00:00:00Z', {})

    def test_after_with_invalid_value_type(self):
        rule = AfterRule('2024-01-01')
        assert not rule.passes('date', 123, {})
        assert not rule.passes('date', None, {})
        assert not rule.passes('date', [], {})

    def test_after_with_invalid_date_format(self):
        rule = AfterRule('2024-01-01')
        assert not rule.passes('date', 'invalid-date', {})

    def test_after_with_invalid_field_reference_type(self):
        rule = AfterRule('start_date')
        data = {'start_date': 123}
        assert not rule.passes('end_date', '2024-01-02', data)

    def test_after_message(self):
        rule = AfterRule('2024-01-01')
        assert "after 2024-01-01" in rule.message()


class TestAfterOrEqualRule:
    def test_after_or_equal_with_same_date(self):
        rule = AfterOrEqualRule('2024-01-01')
        assert rule.passes('date', '2024-01-01', {})

    def test_after_or_equal_with_later_date(self):
        rule = AfterOrEqualRule('2024-01-01')
        assert rule.passes('date', '2024-01-02', {})

    def test_after_or_equal_with_earlier_date(self):
        rule = AfterOrEqualRule('2024-01-01')
        assert not rule.passes('date', '2023-12-31', {})

    def test_after_or_equal_with_field_reference(self):
        rule = AfterOrEqualRule('start_date')
        data = {'start_date': '2024-01-01'}
        assert rule.passes('end_date', '2024-01-01', data)
        assert rule.passes('end_date', '2024-01-02', data)
        assert not rule.passes('end_date', '2023-12-31', data)

    def test_after_or_equal_with_datetime_objects(self):
        rule = AfterOrEqualRule('start_date')
        data = {'start_date': datetime(2024, 1, 1)}
        assert rule.passes('end_date', datetime(2024, 1, 1), data)

    def test_after_or_equal_with_today(self):
        rule = AfterOrEqualRule('today')
        today = datetime.now().strftime('%Y-%m-%d')
        assert rule.passes('date', today, {})

    def test_after_or_equal_with_invalid_types(self):
        rule = AfterOrEqualRule('2024-01-01')
        assert not rule.passes('date', 123, {})
        assert not rule.passes('date', None, {})


class TestBeforeRule:
    def test_before_with_static_date(self):
        rule = BeforeRule('2024-12-31')
        assert rule.passes('date', '2024-01-01', {})
        assert not rule.passes('date', '2025-01-01', {})
        assert not rule.passes('date', '2024-12-31', {})

    def test_before_with_field_reference(self):
        rule = BeforeRule('end_date')
        data = {'end_date': '2024-12-31', 'start_date': '2024-01-01'}
        assert rule.passes('start_date', '2024-01-01', data)
        assert not rule.passes('start_date', '2025-01-01', data)

    def test_before_with_datetime_value(self):
        rule = BeforeRule('2024-12-31')
        date_obj = datetime(2024, 1, 1, 10, 30)
        assert rule.passes('date', date_obj, {})

    def test_before_with_today_keyword(self):
        rule = BeforeRule('today')
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
        assert rule.passes('date', yesterday, {})
        assert not rule.passes('date', tomorrow, {})

    def test_before_with_tomorrow_keyword(self):
        rule = BeforeRule('tomorrow')
        today = datetime.now().strftime('%Y-%m-%d')
        assert rule.passes('date', today, {})

    def test_before_with_yesterday_keyword(self):
        rule = BeforeRule('yesterday')
        old_date = (datetime.now() - timedelta(days=2)).strftime('%Y-%m-%d')
        assert rule.passes('date', old_date, {})

    def test_before_with_datetime_field_reference(self):
        rule = BeforeRule('end_date')
        data = {'end_date': datetime(2024, 12, 31)}
        assert rule.passes('start_date', datetime(2024, 1, 1), data)

    def test_before_with_invalid_types(self):
        rule = BeforeRule('2024-12-31')
        assert not rule.passes('date', 123, {})
        assert not rule.passes('date', None, {})
        assert not rule.passes('date', 'invalid-date', {})


class TestBeforeOrEqualRule:
    def test_before_or_equal_with_same_date(self):
        rule = BeforeOrEqualRule('2024-12-31')
        assert rule.passes('date', '2024-12-31', {})

    def test_before_or_equal_with_earlier_date(self):
        rule = BeforeOrEqualRule('2024-12-31')
        assert rule.passes('date', '2024-01-01', {})

    def test_before_or_equal_with_later_date(self):
        rule = BeforeOrEqualRule('2024-12-31')
        assert not rule.passes('date', '2025-01-01', {})

    def test_before_or_equal_with_field_reference(self):
        rule = BeforeOrEqualRule('end_date')
        data = {'end_date': '2024-12-31'}
        assert rule.passes('start_date', '2024-12-31', data)
        assert rule.passes('start_date', '2024-01-01', data)
        assert not rule.passes('start_date', '2025-01-01', data)

    def test_before_or_equal_with_datetime_objects(self):
        rule = BeforeOrEqualRule('end_date')
        data = {'end_date': datetime(2024, 12, 31)}
        assert rule.passes('start_date', datetime(2024, 12, 31), data)

    def test_before_or_equal_with_today(self):
        rule = BeforeOrEqualRule('today')
        today = datetime.now().strftime('%Y-%m-%d')
        assert rule.passes('date', today, {})

    def test_before_or_equal_with_invalid_types(self):
        rule = BeforeOrEqualRule('2024-12-31')
        assert not rule.passes('date', 123, {})
        assert not rule.passes('date', None, {})


class TestDateEqualsRule:
    def test_date_equals_with_same_date(self):
        rule = DateEqualsRule('2024-01-15')
        assert rule.passes('date', '2024-01-15', {})

    def test_date_equals_with_different_date(self):
        rule = DateEqualsRule('2024-01-15')
        assert not rule.passes('date', '2024-01-16', {})
        assert not rule.passes('date', '2024-01-14', {})

    def test_date_equals_with_field_reference(self):
        rule = DateEqualsRule('other_date')
        data = {'other_date': '2024-01-15'}
        assert rule.passes('date', '2024-01-15', data)
        assert not rule.passes('date', '2024-01-16', data)

    def test_date_equals_with_datetime_value(self):
        rule = DateEqualsRule('2024-01-15')
        date_obj = datetime(2024, 1, 15, 10, 30)
        assert rule.passes('date', date_obj, {})

    def test_date_equals_with_datetime_field_reference(self):
        rule = DateEqualsRule('other_date')
        data = {'other_date': datetime(2024, 1, 15)}
        assert rule.passes('date', datetime(2024, 1, 15, 23, 59), data)

    def test_date_equals_ignores_time_component(self):
        rule = DateEqualsRule('other_date')
        data = {'other_date': '2024-01-15T08:00:00'}
        assert rule.passes('date', '2024-01-15T20:00:00', data)

    def test_date_equals_with_iso_format_z_suffix(self):
        rule = DateEqualsRule('2024-01-15T00:00:00Z')
        assert rule.passes('date', '2024-01-15T12:00:00Z', {})

    def test_date_equals_with_invalid_value_type(self):
        rule = DateEqualsRule('2024-01-15')
        assert not rule.passes('date', 123, {})
        assert not rule.passes('date', None, {})
        assert not rule.passes('date', [], {})

    def test_date_equals_with_invalid_date_format(self):
        rule = DateEqualsRule('2024-01-15')
        assert not rule.passes('date', 'invalid-date', {})

    def test_date_equals_with_invalid_field_reference_type(self):
        rule = DateEqualsRule('other_date')
        data = {'other_date': 123}
        assert not rule.passes('date', '2024-01-15', data)

    def test_date_equals_message(self):
        rule = DateEqualsRule('2024-01-15')
        assert "equal to 2024-01-15" in rule.message()


class TestInArrayRule:
    def test_in_array_with_simple_list(self):
        rule = InArrayRule('allowed_values')
        data = {'allowed_values': ['a', 'b', 'c']}
        assert rule.passes('choice', 'a', data)
        assert rule.passes('choice', 'b', data)
        assert not rule.passes('choice', 'd', data)

    def test_in_array_with_dict_values(self):
        rule = InArrayRule('allowed_values')
        data = {'allowed_values': {'key1': 'value1', 'key2': 'value2'}}
        assert rule.passes('choice', 'value1', data)
        assert rule.passes('choice', 'value2', data)
        assert not rule.passes('choice', 'key1', data)

    def test_in_array_with_nested_field(self):
        rule = InArrayRule('settings.allowed_roles')
        data = {'settings': {'allowed_roles': ['admin', 'editor', 'viewer']}}
        assert rule.passes('role', 'admin', data)
        assert not rule.passes('role', 'superadmin', data)

    def test_in_array_with_wildcard_syntax(self):
        rule = InArrayRule('users.*')
        data = {'users': ['alice', 'bob', 'charlie']}
        assert rule.passes('name', 'alice', data)

    def test_in_array_with_non_list_or_dict(self):
        rule = InArrayRule('allowed_values')
        data = {'allowed_values': 'not-a-list'}
        assert not rule.passes('choice', 'a', data)

    def test_in_array_with_missing_field(self):
        rule = InArrayRule('allowed_values')
        data = {}
        assert not rule.passes('choice', 'a', data)

    def test_in_array_with_nested_missing_field(self):
        rule = InArrayRule('settings.allowed_roles')
        data = {'settings': {}}
        assert not rule.passes('role', 'admin', data)

    def test_in_array_with_deep_nesting(self):
        rule = InArrayRule('config.security.allowed_ips')
        data = {'config': {'security': {'allowed_ips': ['192.168.1.1', '10.0.0.1']}}}
        assert rule.passes('ip', '192.168.1.1', data)
        assert not rule.passes('ip', '127.0.0.1', data)

    def test_in_array_with_numeric_values(self):
        rule = InArrayRule('allowed_ports')
        data = {'allowed_ports': [80, 443, 8080]}
        assert rule.passes('port', 80, data)
        assert not rule.passes('port', 3000, data)

    def test_in_array_message(self):
        rule = InArrayRule('allowed_values')
        assert "exist in allowed_values" in rule.message()


class TestBailRule:
    def test_bail_always_passes(self):
        rule = BailRule()
        assert rule.passes('field', 'any value', {})
        assert rule.passes('field', None, {})
        assert rule.passes('field', 123, {})
        assert rule.passes('field', [], {})

    def test_bail_empty_message(self):
        rule = BailRule()
        assert rule.message() == ""


class TestValidatorWithLowCoverageRules:
    def test_validator_with_active_url(self):
        data = {'website': 'https://www.google.com'}
        rules = {'website': 'required|active_url'}
        validator = Validator(data, rules)
        assert validator.passes()

    def test_validator_with_after_rule_and_field_reference(self):
        data = {'start_date': '2024-01-01', 'end_date': '2024-12-31'}
        rules = {'start_date': 'required|date', 'end_date': 'required|date|after:start_date'}
        validator = Validator(data, rules)
        assert validator.passes()

    def test_validator_with_after_rule_failure(self):
        data = {'start_date': '2024-12-31', 'end_date': '2024-01-01'}
        rules = {'start_date': 'required|date', 'end_date': 'required|date|after:start_date'}
        validator = Validator(data, rules)
        assert validator.fails()

    def test_validator_with_before_rule_and_field_reference(self):
        data = {'start_date': '2024-01-01', 'end_date': '2024-12-31'}
        rules = {'start_date': 'required|date|before:end_date', 'end_date': 'required|date'}
        validator = Validator(data, rules)
        assert validator.passes()

    def test_validator_with_date_equals_and_field_reference(self):
        data = {'date1': '2024-01-15', 'date2': '2024-01-15'}
        rules = {'date1': 'required|date', 'date2': 'required|date|date_equals:date1'}
        validator = Validator(data, rules)
        assert validator.passes()

    def test_validator_with_in_array_nested(self):
        data = {'user': {'roles': ['admin', 'editor']}, 'selected_role': 'admin'}
        rules = {'selected_role': 'required|in_array:user.roles'}
        validator = Validator(data, rules)
        assert validator.passes()

    def test_validator_with_in_array_failure(self):
        data = {'allowed': ['a', 'b', 'c'], 'choice': 'd'}
        rules = {'choice': 'required|in_array:allowed'}
        validator = Validator(data, rules)
        assert validator.fails()

    def test_validator_with_bail_stops_validation(self):
        data = {'field': 'invalid'}
        rules = {'field': 'bail|email|min:10'}
        validator = Validator(data, rules)
        assert validator.fails()
        assert validator.errors().count() == 1


class TestComplexDateValidationScenarios:
    def test_event_booking_date_range_validation(self):
        data = {
            'event_start': '2024-06-01',
            'event_end': '2024-06-05',
            'booking_date': '2024-05-15',
            'check_in': '2024-06-01',
            'check_out': '2024-06-05'
        }
        rules = {
            'event_start': 'required|date',
            'event_end': 'required|date|after:event_start',
            'booking_date': 'required|date|before:event_start',
            'check_in': 'required|date|date_equals:event_start',
            'check_out': 'required|date|after_or_equal:check_in|before_or_equal:event_end'
        }
        validator = Validator(data, rules)
        assert validator.passes()

    def test_subscription_period_validation(self):
        today = datetime.now().strftime('%Y-%m-%d')
        future = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
        
        data = {
            'subscription_start': today,
            'subscription_end': future,
            'trial_end': (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')
        }
        rules = {
            'subscription_start': 'required|date|after_or_equal:today',
            'subscription_end': 'required|date|after:subscription_start',
            'trial_end': 'required|date|after:subscription_start|before:subscription_end'
        }
        validator = Validator(data, rules)
        assert validator.passes()

    def test_appointment_scheduling_validation(self):
        tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
        today = datetime.now().strftime('%Y-%m-%d')
        
        data = {
            'appointment_date': tomorrow,
            'earliest_available': today
        }
        rules = {
            'appointment_date': 'required|date|after:today',
            'earliest_available': 'required|date|before_or_equal:today'
        }
        validator = Validator(data, rules)
        assert validator.passes()

    def test_multi_field_date_comparison_validation(self):
        data = {
            'project_proposal': '2024-01-01',
            'project_approval': '2024-01-15',
            'project_start': '2024-02-01',
            'project_milestone': '2024-06-01',
            'project_end': '2024-12-31'
        }
        rules = {
            'project_proposal': 'required|date',
            'project_approval': 'required|date|after:project_proposal',
            'project_start': 'required|date|after:project_approval',
            'project_milestone': 'required|date|after:project_start|before:project_end',
            'project_end': 'required|date|after:project_milestone'
        }
        validator = Validator(data, rules)
        assert validator.passes()

    def test_birth_date_and_anniversary_validation(self):
        data = {
            'birth_date': '1990-05-15',
            'hire_date': '2020-03-01',
            'first_anniversary': '2021-03-01'
        }
        rules = {
            'birth_date': 'required|date|before:today',
            'hire_date': 'required|date|after:birth_date|before:today',
            'first_anniversary': 'required|date|after:hire_date|before_or_equal:today'
        }
        validator = Validator(data, rules)
        assert validator.passes()


class TestComplexInArrayScenarios:
    def test_role_based_permission_validation(self):
        data = {
            'user': {
                'role': 'editor',
                'allowed_roles': ['admin', 'editor', 'author']
            },
            'permissions': ['read', 'write', 'publish'],
            'requested_permission': 'write'
        }
        rules = {
            'user.role': 'required|in_array:user.allowed_roles',
            'requested_permission': 'required|in_array:permissions'
        }
        validator = Validator(data, rules)
        assert validator.passes()

    def test_multi_level_nested_array_validation(self):
        data = {
            'organization': {
                'departments': {
                    'engineering': {
                        'teams': ['backend', 'frontend', 'devops']
                    }
                }
            },
            'assigned_team': 'backend'
        }
        rules = {
            'assigned_team': 'required|in_array:organization.departments.engineering.teams'
        }
        validator = Validator(data, rules)
        assert validator.passes()

    def test_dynamic_options_validation(self):
        data = {
            'available_colors': {'red': 'Red', 'blue': 'Blue', 'green': 'Green'},
            'selected_color': 'Red'
        }
        rules = {
            'selected_color': 'required|in_array:available_colors'
        }
        validator = Validator(data, rules)
        assert validator.passes()

    def test_cascading_array_validation(self):
        data = {
            'category': 'electronics',
            'categories': ['electronics', 'books', 'clothing'],
            'subcategory': 'laptops',
            'electronics_subcategories': ['laptops', 'phones', 'tablets']
        }
        rules = {
            'category': 'required|in_array:categories',
            'subcategory': 'required|in_array:electronics_subcategories'
        }
        validator = Validator(data, rules)
        assert validator.passes()


class TestMixedComplexScenarios:
    def test_travel_booking_comprehensive_validation(self):
        departure_date = (datetime.now() + timedelta(days=14)).strftime('%Y-%m-%d')
        return_date = (datetime.now() + timedelta(days=21)).strftime('%Y-%m-%d')
        
        data = {
            'booking_url': 'https://www.google.com',
            'departure_date': departure_date,
            'return_date': return_date,
            'passenger_count': 2,
            'allowed_passengers': [1, 2, 3, 4, 5, 6],
            'destination': 'Paris',
            'available_destinations': ['London', 'Paris', 'Rome', 'Berlin']
        }
        rules = {
            'booking_url': 'required|active_url',
            'departure_date': 'required|date|after:today',
            'return_date': 'required|date|after:departure_date',
            'passenger_count': 'required|integer|in_array:allowed_passengers',
            'destination': 'required|string|in_array:available_destinations'
        }
        validator = Validator(data, rules)
        assert validator.passes()

    def test_conference_registration_with_dates_and_arrays(self):
        conference_date = (datetime.now() + timedelta(days=60)).strftime('%Y-%m-%d')
        registration_deadline = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
        
        data = {
            'conference_website': 'https://www.github.com',
            'conference_date': conference_date,
            'registration_deadline': registration_deadline,
            'registration_date': datetime.now().strftime('%Y-%m-%d'),
            'selected_track': 'AI/ML',
            'available_tracks': ['Web Development', 'AI/ML', 'DevOps', 'Security'],
            'dietary_preference': 'vegetarian',
            'meal_options': ['vegetarian', 'vegan', 'gluten-free', 'none']
        }
        rules = {
            'conference_website': 'required|active_url',
            'conference_date': 'required|date|after:today',
            'registration_deadline': 'required|date|after:registration_date|before:conference_date',
            'registration_date': 'required|date|before_or_equal:today',
            'selected_track': 'required|in_array:available_tracks',
            'dietary_preference': 'required|in_array:meal_options'
        }
        validator = Validator(data, rules)
        assert validator.passes()

    def test_project_milestone_with_dependencies(self):
        data = {
            'project_website': 'https://github.com/example/project',
            'milestone1_start': '2024-01-01',
            'milestone1_end': '2024-03-31',
            'milestone2_start': '2024-04-01',
            'milestone2_end': '2024-06-30',
            'milestone3_start': '2024-07-01',
            'milestone3_end': '2024-12-31',
            'milestone1_status': 'completed',
            'milestone_statuses': ['completed', 'in_progress', 'pending'],
            'priority': 'high',
            'priorities': ['low', 'medium', 'high', 'critical']
        }
        rules = {
            'project_website': 'required|active_url',
            'milestone1_start': 'required|date',
            'milestone1_end': 'required|date|after:milestone1_start',
            'milestone2_start': 'required|date|date_equals:milestone1_end',
            'milestone2_end': 'required|date|after:milestone2_start',
            'milestone3_start': 'required|date|after:milestone2_end',
            'milestone3_end': 'required|date|after:milestone3_start',
            'milestone1_status': 'required|in_array:milestone_statuses',
            'priority': 'required|in_array:priorities'
        }
        validator = Validator(data, rules)
        
        data['milestone2_start'] = '2024-03-31'
        validator = Validator(data, rules)
        assert validator.passes()

    def test_medical_appointment_scheduling(self):
        tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
        next_week = (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')
        
        data = {
            'hospital_website': 'https://www.google.com',
            'appointment_date': next_week,
            'earliest_date': tomorrow,
            'department': 'cardiology',
            'available_departments': ['cardiology', 'neurology', 'orthopedics', 'pediatrics'],
            'doctor': 'Dr. Smith',
            'cardiology_doctors': ['Dr. Smith', 'Dr. Johnson', 'Dr. Williams'],
            'time_slot': '10:00 AM',
            'available_slots': ['09:00 AM', '10:00 AM', '11:00 AM', '02:00 PM', '03:00 PM']
        }
        rules = {
            'hospital_website': 'required|active_url',
            'appointment_date': 'required|date|after:today|after_or_equal:earliest_date',
            'earliest_date': 'required|date|after:today',
            'department': 'required|in_array:available_departments',
            'doctor': 'required|in_array:cardiology_doctors',
            'time_slot': 'required|in_array:available_slots'
        }
        validator = Validator(data, rules)
        assert validator.passes()

    def test_e_commerce_order_with_complex_validations(self):
        delivery_date = (datetime.now() + timedelta(days=5)).strftime('%Y-%m-%d')
        
        data = {
            'store_url': 'https://www.github.com',
            'order_date': datetime.now().strftime('%Y-%m-%d'),
            'expected_delivery': delivery_date,
            'shipping_method': 'express',
            'available_shipping': ['standard', 'express', 'overnight'],
            'payment_method': 'credit_card',
            'accepted_payments': ['credit_card', 'debit_card', 'paypal', 'bank_transfer'],
            'country': 'US',
            'shipping_countries': ['US', 'CA', 'UK', 'AU'],
            'warehouse_location': 'United States',
            'warehouses': {
                'warehouse_us': 'United States',
                'warehouse_ca': 'Canada',
                'warehouse_uk': 'United Kingdom'
            }
        }
        rules = {
            'store_url': 'required|active_url',
            'order_date': 'required|date|before_or_equal:today',
            'expected_delivery': 'required|date|after:order_date',
            'shipping_method': 'required|in_array:available_shipping',
            'payment_method': 'required|in_array:accepted_payments',
            'country': 'required|in_array:shipping_countries',
            'warehouse_location': 'required|in_array:warehouses'
        }
        validator = Validator(data, rules)
        assert validator.passes()

    def test_employee_onboarding_workflow(self):
        start_date = (datetime.now() + timedelta(days=14)).strftime('%Y-%m-%d')
        orientation_date = (datetime.now() + timedelta(days=13)).strftime('%Y-%m-%d')
        
        data = {
            'company_website': 'https://www.example-company.com',
            'hire_date': datetime.now().strftime('%Y-%m-%d'),
            'start_date': start_date,
            'orientation_date': orientation_date,
            'department': 'engineering',
            'departments': ['hr', 'engineering', 'sales', 'marketing'],
            'position': 'senior_engineer',
            'engineering_positions': ['intern', 'junior_engineer', 'engineer', 'senior_engineer', 'lead_engineer'],
            'manager': 'John Doe',
            'engineering_managers': ['John Doe', 'Jane Smith', 'Bob Johnson'],
            'office_location': 'New York',
            'offices': ['New York', 'San Francisco', 'Austin', 'Remote']
        }
        rules = {
            'company_website': 'required|active_url',
            'hire_date': 'required|date|before_or_equal:today',
            'start_date': 'required|date|after:hire_date',
            'orientation_date': 'required|date|after:hire_date|before:start_date',
            'department': 'required|in_array:departments',
            'position': 'required|in_array:engineering_positions',
            'manager': 'required|in_array:engineering_managers',
            'office_location': 'required|in_array:offices'
        }
        validator = Validator(data, rules)
        assert validator.passes()
