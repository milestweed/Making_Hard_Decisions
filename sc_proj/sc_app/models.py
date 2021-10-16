from django.db import models

# Create your models here.
class Colors(models.Model):

    brand = models.TextField(max_length=100, primary_key=True)
    hex = models.CharField(max_length=7, unique=True)

    class Meta:

        verbose_name_plural = 'Colors'

    def __str__(self):
        return self.brand

class Info(models.Model):

    sg_id = models.TextField(max_length=50, primary_key=True)
    address = models.CharField(max_length=250)
    name = models.ForeignKey(Colors,
                            on_delete=models.CASCADE,
                            related_name='+')
    lat = models.FloatField()
    lon = models.FloatField()
    sq_ft = models.FloatField()
    p_lot = models.BooleanField()
    category = models.CharField(max_length=100)

    class Meta:

        verbose_name_plural = 'Info'

    def __str__(self):

        return self.sg_id

class Closed(models.Model):

    name = models.TextField(max_length=3, primary_key=True)
    id = models.ForeignKey(Info,
                            on_delete=models.CASCADE,
                            related_name='+')

    class Meta:

        verbose_name_plural = 'Closed'

    def __str__(self):

        return self.name

class Movement(models.Model):

    id = models.AutoField(primary_key=True)
    open_store = models.ForeignKey(Info,
                                on_delete=models.CASCADE,
                                related_name="+")
    closed_store = models.ForeignKey(Info,
                                on_delete=models.CASCADE,
                                related_name='+')
    movement = models.FloatField()
    yr = models.IntegerField(default=0)


    def __str__(self):

        return(str(self.id))


class Cbgs(models.Model):

    cbgID = models.IntegerField(primary_key=True, null=False)
    population = models.IntegerField()
    median_income = models.FloatField()

    class Meta:

        verbose_name_plural = 'CBGs'


    def __str__(self):

        return(str(self.cbgID))


class CbgStore(models.Model):

    ID = models.AutoField(primary_key=True)
    cbgID = models.ForeignKey(Cbgs,
                            on_delete = models.CASCADE,
                            related_name = "+")
    storeID = models.ForeignKey(Info,
                            on_delete = models.CASCADE,
                            related_name = "+")
    percent_visit = models.FloatField()
    number_visits = models.IntegerField()
    pop_near_store = models.FloatField()
    dist_store_cbg = models.FloatField()
    store_area = models.IntegerField()
    p_lot = models.BooleanField()
    poi_near_store = models.IntegerField()
    diversity_near_store = models.FloatField()
    demo_similarity = models.FloatField()
    med_inc_near_store = models.FloatField()
    brand = models.CharField(max_length= 80)
    num_visit_brand = models.IntegerField()
    percent_visit_brand = models.FloatField()
    year = models.IntegerField()

    def __str__(self):

        return('Connection: ' + str(self.ID))
