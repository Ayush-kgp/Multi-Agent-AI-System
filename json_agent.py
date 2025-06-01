import json
from typing import Dict, Any, List, Optional
from base_agent import BaseAgent
from pydantic import BaseModel, ValidationError, create_model

class JSONAgent(BaseAgent):
    def process(self, data: str, conversation_id: str) -> Dict[str, Any]:
        """Process JSON input and extract/validate fields"""
        try:
            # Parse JSON
            json_data = json.loads(data)
            
            # Infer schema from data
            schema = self._infer_schema(json_data)
            
            # Validate and transform data
            validated_data = self._validate_data(json_data, schema)
            
            # Check for anomalies
            anomalies = self._check_anomalies(json_data)
            
            result = {
                'validated_data': validated_data,
                'schema': schema,
                'anomalies': anomalies,
                'status': 'success' if not anomalies else 'warning'
            }

            # Log the processing
            self.log_action(
                conversation_id=conversation_id,
                action='process_json',
                details={
                    'schema': schema,
                    'anomalies_found': len(anomalies),
                    'status': result['status']
                }
            )

            # Update context
            self.update_context(conversation_id, {
                'json_schema': schema,
                'anomalies': anomalies,
                'processing_status': result['status']
            })

            return result

        except json.JSONDecodeError as e:
            error_result = {
                'status': 'error',
                'error': f'Invalid JSON format: {str(e)}'
            }
            self.log_action(
                conversation_id=conversation_id,
                action='process_json_error',
                details=error_result
            )
            return error_result

    def _infer_schema(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Infer the schema from the JSON data"""
        def get_type(value: Any) -> str:
            if isinstance(value, bool):
                return 'boolean'
            elif isinstance(value, int):
                return 'integer'
            elif isinstance(value, float):
                return 'number'
            elif isinstance(value, str):
                return 'string'
            elif isinstance(value, list):
                return 'array'
            elif isinstance(value, dict):
                return 'object'
            elif value is None:
                return 'null'
            return 'unknown'

        def infer_field(value: Any) -> Dict[str, Any]:
            field_type = get_type(value)
            schema = {'type': field_type}
            
            if field_type == 'object':
                schema['properties'] = {
                    k: infer_field(v) for k, v in value.items()
                }
            elif field_type == 'array' and value:
                schema['items'] = infer_field(value[0])
                
            return schema

        return infer_field(data)

    def _validate_data(self, data: Dict[str, Any], schema: Dict[str, Any]) -> Dict[str, Any]:
        """Validate data against the inferred schema"""
        def create_pydantic_model(schema: Dict[str, Any], name: str = 'DynamicModel') -> BaseModel:
            fields = {}
            for field_name, field_schema in schema.get('properties', {}).items():
                field_type = field_schema['type']
                if field_type == 'object':
                    fields[field_name] = (
                        create_pydantic_model(field_schema, f'{name}_{field_name}'),
                        ...
                    )
                else:
                    python_type = {
                        'string': str,
                        'integer': int,
                        'number': float,
                        'boolean': bool,
                        'null': None,
                        'array': List,
                        'unknown': Any
                    }.get(field_type, Any)
                    fields[field_name] = (python_type, ...)

            return create_model(name, **fields)

        try:
            model = create_pydantic_model(schema)
            return model(**data).dict()
        except ValidationError as e:
            return {'validation_errors': str(e)}

    def _check_anomalies(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check for potential anomalies in the data"""
        anomalies = []

        def check_value(value: Any, path: str) -> None:
            if isinstance(value, dict):
                # Check for empty objects
                if not value:
                    anomalies.append({
                        'type': 'empty_object',
                        'path': path
                    })
                for k, v in value.items():
                    check_value(v, f"{path}.{k}" if path else k)
            elif isinstance(value, list):
                # Check for empty lists
                if not value:
                    anomalies.append({
                        'type': 'empty_array',
                        'path': path
                    })
                # Check for inconsistent types in arrays
                if value:
                    base_type = type(value[0])
                    for i, item in enumerate(value):
                        if not isinstance(item, base_type):
                            anomalies.append({
                                'type': 'inconsistent_array_type',
                                'path': f"{path}[{i}]",
                                'expected': base_type.__name__,
                                'found': type(item).__name__
                            })
            elif value is None:
                # Flag null values
                anomalies.append({
                    'type': 'null_value',
                    'path': path
                })

        check_value(data, "")
        return anomalies 