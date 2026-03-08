from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from django.db.models import Sum, Q
from decimal import Decimal
from .models import Vacancy, Urgency, VacancyStatus
from .serializers import (
    VacancySerializer, VacancyListSerializer, 
    ChangeStatusSerializer, VacancyStatsSerializer,
    CostSimulationSerializer, CostSimulationResultSerializer
)
import uuid

class VacancyViewSet(viewsets.ModelViewSet):
    """
    ViewSet para CRUD completo de Vagas com UUID
    """
    queryset = Vacancy.objects.all()
    serializer_class = VacancySerializer
    lookup_field = 'pk'
    
    def get_serializer_class(self):
        """Retorna serializer diferente para cada ação"""
        if self.action == 'list':
            return VacancyListSerializer
        elif self.action == 'change_status':
            return ChangeStatusSerializer
        elif self.action in ['simulate_costs', 'simulate_costs_get']:
            return CostSimulationSerializer
        return VacancySerializer
    
    @swagger_auto_schema(
        operation_description="Lista todas as vagas com opção de filtrar",
        manual_parameters=[
            openapi.Parameter(
                'status', openapi.IN_QUERY,
                description="Filtrar por status (E, F, C)",
                type=openapi.TYPE_STRING,
                enum=['E', 'F', 'C']
            ),
            openapi.Parameter(
                'urgency', openapi.IN_QUERY,
                description="Filtrar por urgência (0, 1, 2)",
                type=openapi.TYPE_INTEGER,
                enum=[0, 1, 2]
            ),
            openapi.Parameter(
                'sector', openapi.IN_QUERY,
                description="Filtrar por setor (busca parcial)",
                type=openapi.TYPE_STRING
            ),
        ]
    )
    def list(self, request, *args, **kwargs):
        """Lista todas as vagas com filtros"""
        queryset = self.get_queryset()
        
        # Filtros
        status_param = request.query_params.get('status')
        if status_param and status_param in dict(VacancyStatus.choices):
            queryset = queryset.filter(status=status_param)
        
        urgency_param = request.query_params.get('urgency')
        if urgency_param and urgency_param.isdigit():
            queryset = queryset.filter(urgency=int(urgency_param))
        
        sector_param = request.query_params.get('sector')
        if sector_param:
            queryset = queryset.filter(sector__icontains=sector_param)
        
        # Aplicar ordenação padrão
        queryset = queryset.order_by('-created_at')
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @swagger_auto_schema(
        operation_description="Cria uma nova vaga",
        request_body=VacancySerializer,
        responses={201: VacancySerializer()}
    )
    def create(self, request, *args, **kwargs):
        """Cria uma nova vaga"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        
        return Response({
            'message': 'Vaga criada com sucesso',
            'data': serializer.data
        }, status=status.HTTP_201_CREATED)
    
    @swagger_auto_schema(
        operation_description="Retorna detalhes de uma vaga específica",
        responses={200: VacancySerializer()}
    )
    def retrieve(self, request, *args, **kwargs):
        """Retorna detalhes de uma vaga"""
        return super().retrieve(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_description="Atualiza todos os campos de uma vaga",
        request_body=VacancySerializer,
        responses={200: VacancySerializer()}
    )
    def update(self, request, *args, **kwargs):
        """Atualiza todos os campos de uma vaga"""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        
        return Response({
            'message': 'Vaga atualizada com sucesso',
            'data': serializer.data
        })
    
    @swagger_auto_schema(
        operation_description="Atualiza parcialmente uma vaga",
        request_body=VacancySerializer,
        responses={200: VacancySerializer()}
    )
    def partial_update(self, request, *args, **kwargs):
        """Atualiza campos específicos de uma vaga"""
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_description="Remove uma vaga",
        responses={204: "Vaga removida"}
    )
    def destroy(self, request, *args, **kwargs):
        """Remove uma vaga do sistema"""
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response({
            'message': 'Vaga removida com sucesso'
        }, status=status.HTTP_204_NO_CONTENT)
    
    @swagger_auto_schema(
        operation_description="Retorna estatísticas das vagas",
        responses={200: VacancyStatsSerializer()}
    )
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Retorna estatísticas consolidadas"""
        total = Vacancy.objects.count()
        ongoing = Vacancy.objects.filter(status=VacancyStatus.ONGOING).count()
        finalized = Vacancy.objects.filter(status=VacancyStatus.FINALIZED).count()
        cancelled = Vacancy.objects.filter(status=VacancyStatus.CANCELLED).count()
        high_urgency = Vacancy.objects.filter(urgency=Urgency.HIGH).count()
        
        data = {
            'total': total,
            'ongoing': ongoing,
            'finalized': finalized,
            'cancelled': cancelled,
            'high_urgency': high_urgency
        }
        
        serializer = VacancyStatsSerializer(data)
        return Response(serializer.data)
    
    @swagger_auto_schema(
        operation_description="Altera o status de uma vaga",
        request_body=ChangeStatusSerializer,
        responses={200: VacancySerializer()}
    )
    @action(detail=True, methods=['patch'])
    def change_status(self, request, pk=None):
        """Altera apenas o status de uma vaga"""
        vacancy = self.get_object()
        
        status_serializer = self.get_serializer(data=request.data)
        status_serializer.is_valid(raise_exception=True)
        
        new_status = status_serializer.validated_data['status']
        vacancy.status = new_status
        vacancy.save()
        
        response_serializer = VacancySerializer(vacancy)
        return Response({
            'message': f'Status alterado com sucesso!',
            'data': response_serializer.data
        })
    
    @swagger_auto_schema(
        operation_description="Simula custos das vagas em andamento com filtros",
        method='post',
        request_body=CostSimulationSerializer,
        responses={
            200: CostSimulationResultSerializer(),
            400: "Erro nos parâmetros enviados"
        }
    )
    @action(detail=False, methods=['post'], url_path='simulate-costs')
    def simulate_costs(self, request):
     
        simulation_serializer = self.get_serializer(data=request.data)
        simulation_serializer.is_valid(raise_exception=True)
        
        # Extrair dados validados
        sector = simulation_serializer.validated_data.get('sector', '')
        period = simulation_serializer.validated_data.get('period', 'annual')
        
        # Base queryset: apenas vagas EM ANDAMENTO (status 'E')
        queryset = Vacancy.objects.filter(status=VacancyStatus.ONGOING)
        
        # Aplicar filtro de setor se fornecido
        if sector and sector.strip():
            queryset = queryset.filter(sector__icontains=sector.strip())
        
        # Verificar se há vagas
        vacancies_count = queryset.count()
        
        if vacancies_count == 0:
            filter_msg = f" para o setor '{sector}'" if sector else ""
            return Response({
                'total_cost': 0,
                'formatted_cost': 'R$ 0,00',
                'vacancies_count': 0,
                'period': 'Mensal' if period == 'monthly' else 'Anual',
                'sector_filter': sector if sector else None,
                'message': f"Não existem vagas em andamento{filter_msg}",
                'vacancies': []
            }, status=status.HTTP_200_OK)
        
        # Calcular soma dos salários
        total_salary = queryset.aggregate(
            total=Sum('salary_expectation')
        )['total'] or Decimal('0.00')
        
        # Calcular conforme período
        if period == 'annual':
            total_cost = total_salary * 12  # Anual: salário * 12 meses
            period_text = "Anual"
        else:  # monthly
            total_cost = total_salary  # Mensal: soma dos salários
            period_text = "Mensal"
        
        # Formatar valores
        formatted_cost = f"R$ {total_cost:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
        
        # Preparar mensagem de resultado
        sector_msg = f" para o setor '{sector}'" if sector else ""
        message = f"Custo total estimado ({period_text}){sector_msg}: {formatted_cost}"
        
        # Serializar vagas para retornar na resposta
        vacancies_serializer = VacancyListSerializer(queryset, many=True)
        
        # Retornar resultado
        return Response({
            'total_cost': total_cost,
            'formatted_cost': formatted_cost,
            'vacancies_count': vacancies_count,
            'period': period_text,
            'sector_filter': sector if sector else None,
            'message': message,
            'vacancies': vacancies_serializer.data
        }, status=status.HTTP_200_OK)
    
    @swagger_auto_schema(
        operation_description="Versão GET da simulação de custos",
        manual_parameters=[
            openapi.Parameter(
                'sector', openapi.IN_QUERY,
                description="Filtrar por setor",
                type=openapi.TYPE_STRING,
                required=False
            ),
            openapi.Parameter(
                'period', openapi.IN_QUERY,
                description="Período (monthly ou annual)",
                type=openapi.TYPE_STRING,
                enum=['monthly', 'annual'],
                default='annual',
                required=False
            ),
        ],
        responses={200: CostSimulationResultSerializer()}
    )
    @simulate_costs.mapping.get
    def simulate_costs_get(self, request):
       
        data = {
            'sector': request.query_params.get('sector', ''),
            'period': request.query_params.get('period', 'annual')
        }
        
        # Validar dados
        simulation_serializer = self.get_serializer(data=data)
        simulation_serializer.is_valid(raise_exception=True)
        
        # Extrair dados validados
        sector = simulation_serializer.validated_data.get('sector', '')
        period = simulation_serializer.validated_data.get('period', 'annual')
        
        # Base queryset: apenas vagas EM ANDAMENTO
        queryset = Vacancy.objects.filter(status=VacancyStatus.ONGOING)
        
        if sector and sector.strip():
            queryset = queryset.filter(sector__icontains=sector.strip())
        
        vacancies_count = queryset.count()
        
        if vacancies_count == 0:
            filter_msg = f" para o setor '{sector}'" if sector else ""
            return Response({
                'total_cost': 0,
                'formatted_cost': 'R$ 0,00',
                'vacancies_count': 0,
                'period': 'Mensal' if period == 'monthly' else 'Anual',
                'sector_filter': sector if sector else None,
                'message': f"Não existem vagas em andamento{filter_msg}",
                'vacancies': []
            })
        
        total_salary = queryset.aggregate(
            total=Sum('salary_expectation')
        )['total'] or Decimal('0.00')
        
        if period == 'annual':
            total_cost = total_salary * 12
            period_text = "Anual"
        else:
            total_cost = total_salary
            period_text = "Mensal"
        
        formatted_cost = f"R$ {total_cost:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
        sector_msg = f" para o setor '{sector}'" if sector else ""
        message = f"Custo total estimado ({period_text}){sector_msg}: {formatted_cost}"
        
        vacancies_serializer = VacancyListSerializer(queryset, many=True)
        
        return Response({
            'total_cost': total_cost,
            'formatted_cost': formatted_cost,
            'vacancies_count': vacancies_count,
            'period': period_text,
            'sector_filter': sector if sector else None,
            'message': message,
            'vacancies': vacancies_serializer.data
        })