from rest_framework import serializers
from .models import Vacancy, Urgency, VacancyStatus

class VacancySerializer(serializers.ModelSerializer):
    # Mapeamento explícito dos campos camelCase para snake_case
    salaryExpectation = serializers.DecimalField(
        source='salary_expectation',
        max_digits=10,
        decimal_places=2,
        required=True
    )
    startDate = serializers.DateField(
        source='start_date',
        required=True,
        input_formats=['%Y-%m-%d']
    )
    endDate = serializers.DateField(
        source='end_date',
        required=False,
        allow_null=True,
        input_formats=['%Y-%m-%d']
    )
    
    # Campos de display
    urgency_display = serializers.CharField(source='get_urgency_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Vacancy
        fields = [
            'id', 'code', 'description', 'sector', 'manager',
            'salaryExpectation', 'urgency', 'urgency_display',
            'status', 'status_display', 'startDate', 'endDate', 
            'notes', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def to_representation(self, instance):
        """Converte snake_case para camelCase na resposta"""
        data = super().to_representation(instance)
        
        # Mapeamento de campos que precisam ser renomeados
        mapping = {
            'created_at': 'createdAt',
            'updated_at': 'updatedAt',
        }
        
        for old_name, new_name in mapping.items():
            if old_name in data:
                data[new_name] = data.pop(old_name)
        
        return data

class VacancyListSerializer(serializers.ModelSerializer):
    salaryExpectation = serializers.DecimalField(
        source='salary_expectation',
        max_digits=10,
        decimal_places=2
    )
    startDate = serializers.DateField(source='start_date')
    endDate = serializers.DateField(source='end_date', allow_null=True)
    notes = serializers.CharField(allow_blank=True, allow_null=True)
    urgency_display = serializers.CharField(source='get_urgency_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    createdAt = serializers.DateTimeField(source='created_at', read_only=True)
    updatedAt = serializers.DateTimeField(source='updated_at', read_only=True)

    class Meta:
        model = Vacancy
        fields = [
            'id', 'code', 'description', 'sector', 'manager',
            'salaryExpectation', 'urgency', 'urgency_display',
            'status', 'status_display', 'startDate', 'endDate',
            'notes', 'createdAt', 'updatedAt'
        ]

class ChangeStatusSerializer(serializers.Serializer):
    status = serializers.ChoiceField(
        choices=[('E', 'Em Andamento'), ('F', 'Finalizado'), ('C', 'Cancelado')]
    )

class VacancyStatsSerializer(serializers.Serializer):
    total = serializers.IntegerField()
    ongoing = serializers.IntegerField()
    finalized = serializers.IntegerField()
    cancelled = serializers.IntegerField()
    high_urgency = serializers.IntegerField()

class CostSimulationSerializer(serializers.Serializer):
    """Serializer para a simulação de custos"""
    sector = serializers.CharField(required=False, allow_blank=True, help_text="Filtrar por setor")
    period = serializers.ChoiceField(
        choices=[('monthly', 'Mensal'), ('annual', 'Anual')],
        default='annual',
        help_text="Período do cálculo"
    )
    
class CostSimulationResultSerializer(serializers.Serializer):
    """Serializer para o resultado da simulação"""
    total_cost = serializers.DecimalField(max_digits=15, decimal_places=2)
    formatted_cost = serializers.CharField()
    vacancies_count = serializers.IntegerField()
    period = serializers.CharField()
    sector_filter = serializers.CharField(allow_null=True)
    message = serializers.CharField()
    vacancies = VacancyListSerializer(many=True, read_only=True)