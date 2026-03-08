import uuid
from django.db import models
from django.core.validators import MinValueValidator

class Urgency(models.IntegerChoices):
    LOW = 0, 'Baixa'
    MEDIUM = 1, 'Média'
    HIGH = 2, 'Alta'

class VacancyStatus(models.TextChoices):
    ONGOING = 'E', 'Em Andamento'
    FINALIZED = 'F', 'Finalizado'
    CANCELLED = 'C', 'Cancelado'

class Vacancy(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField('Código', max_length=50, unique=True)
    description = models.TextField('Descrição')
    sector = models.CharField('Setor', max_length=100)
    manager = models.CharField('Gestor', max_length=100)
    salary_expectation = models.DecimalField(
        'Expectativa Salarial',
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    urgency = models.IntegerField(
        'Urgência',
        choices=Urgency.choices,
        default=Urgency.LOW
    )
    status = models.CharField(
        'Status',
        max_length=1,
        choices=VacancyStatus.choices,
        default=VacancyStatus.ONGOING
    )
    start_date = models.DateField('Data de Início')
    end_date = models.DateField('Data de Término', null=True, blank=True)
    notes = models.TextField('Observações', null=True, blank=True)
    
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    updated_at = models.DateTimeField('Atualizado em', auto_now=True)

    class Meta:
        verbose_name = 'Vaga'
        verbose_name_plural = 'Vagas'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.code} - {self.description[:50]}"