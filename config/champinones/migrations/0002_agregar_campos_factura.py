# Generated migration for factura improvements
from django.db import migrations, models
import django.core.validators
from decimal import Decimal


class Migration(migrations.Migration):

    dependencies = [
        ('champinones', '0001_initial'),
    ]

    operations = [
        # Agregar campos de factura al modelo Boleto
        migrations.AddField(
            model_name='boleto',
            name='numero_factura',
            field=models.CharField(
                blank=True,
                editable=False,
                help_text='Generado automáticamente',
                max_length=20,
                null=True,
                unique=True,
                verbose_name='Número de Factura'
            ),
        ),
        migrations.AddField(
            model_name='boleto',
            name='subtotal',
            field=models.DecimalField(
                decimal_places=2,
                default=Decimal('0.00'),
                max_digits=8,
                validators=[django.core.validators.MinValueValidator(0)],
                verbose_name='Subtotal (BOB)'
            ),
        ),
        migrations.AddField(
            model_name='boleto',
            name='impuesto_iva',
            field=models.DecimalField(
                decimal_places=2,
                default=Decimal('0.00'),
                max_digits=8,
                validators=[django.core.validators.MinValueValidator(0)],
                verbose_name='IVA 13% (BOB)'
            ),
        ),
        migrations.AddField(
            model_name='boleto',
            name='descuento',
            field=models.DecimalField(
                decimal_places=2,
                default=Decimal('0.00'),
                max_digits=8,
                validators=[django.core.validators.MinValueValidator(0)],
                verbose_name='Descuento (BOB)'
            ),
        ),
        migrations.AddField(
            model_name='boleto',
            name='total_factura',
            field=models.DecimalField(
                decimal_places=2,
                default=Decimal('0.00'),
                editable=False,
                max_digits=8,
                verbose_name='Total Factura (BOB)'
            ),
        ),
        migrations.AddField(
            model_name='boleto',
            name='metodo_pago',
            field=models.CharField(
                choices=[
                    ('EFECTIVO', 'Efectivo'),
                    ('TARJETA', 'Tarjeta'),
                    ('SALDO_VIP', 'Saldo VIP'),
                    ('OTRO', 'Otro'),
                ],
                default='EFECTIVO',
                max_length=20,
                verbose_name='Método de Pago'
            ),
        ),
        migrations.AddField(
            model_name='boleto',
            name='referencia_pago',
            field=models.CharField(
                blank=True,
                max_length=50,
                verbose_name='Referencia de Pago (transacción, talón, etc.)'
            ),
        ),
        migrations.AddField(
            model_name='boleto',
            name='observaciones',
            field=models.TextField(
                blank=True,
                verbose_name='Observaciones'
            ),
        ),
    ]
