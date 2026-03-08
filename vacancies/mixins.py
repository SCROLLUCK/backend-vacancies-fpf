class CamelCaseSerializerMixin:
    """
    Mixin para serializers que converte automaticamente entre camelCase e snake_case
    """
    
    def to_representation(self, instance):
        """Converte snake_case para camelCase na resposta"""
        data = super().to_representation(instance)
        
        # Mapeamento de campos que precisam ser convertidos
        field_mapping = {
            'salary_expectation': 'salaryExpectation',
            'start_date': 'startDate',
            'end_date': 'endDate',
            'created_at': 'createdAt',
            'updated_at': 'updatedAt',
        }
        
        result = {}
        for key, value in data.items():
            # Se for um campo mapeado, usa o nome camelCase
            if key in field_mapping:
                result[field_mapping[key]] = value
            # Senão, mantém o nome original
            else:
                result[key] = value
        
        return result
    
    def to_internal_value(self, data):
        """Converte camelCase para snake_case na requisição"""
        # Mapeamento reverso
        reverse_mapping = {
            'salaryExpectation': 'salary_expectation',
            'startDate': 'start_date',
            'endDate': 'end_date',
        }
        
        converted_data = {}
        for key, value in data.items():
            # Se for um campo mapeado, usa o nome snake_case
            if key in reverse_mapping:
                converted_data[reverse_mapping[key]] = value
            # Senão, mantém o nome original
            elif key not in ['id']:  # Ignora o campo id se vier null
                converted_data[key] = value
        
        return super().to_internal_value(converted_data)