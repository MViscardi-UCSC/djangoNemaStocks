from django.db import models


class Strain(models.Model):
    wja = models.IntegerField(unique=True)
    phenotype = models.CharField(max_length=255, null=True, editable=True)
    description = models.CharField(max_length=255, null=True, editable=True)
    date_created = models.DateField(auto_now_add=True, editable=True)
    
    def active_tubes(self):
        return self.tube_set.filter(thawed=False)
    
    def active_tubes_count(self):
        return self.active_tubes().count()
    
    def inactive_tubes(self):
        return self.tube_set.filter(thawed=True)
    
    def inactive_tubes_count(self):
        return self.inactive_tubes().count()
    
    def total_tubes(self):
        return self.tube_set.all()
    
    def total_tubes_count(self):
        return self.total_tubes().count()
    
    def formatted_WJA(self):
        return f'WJA{self.wja:0>4}'
    
    def __repr__(self):
        return f'Strain(WJA{self.wja:0>4}, ' \
               f'ID-{self.id:0>6}, ' \
               f'Tubes-{self.active_tubes_count()}/{self.total_tubes_count()})'
    
    def repr(self):
        return self.__repr__()
    
    def __str__(self):
        return self.__repr__()


class Tube(models.Model):
    cap_color = models.CharField(max_length=50, default='N/A')
    date_created = models.DateField(auto_now_add=True, editable=True)
    date_thawed = models.DateField(null=True, editable=True)
    box = models.ForeignKey('Box', on_delete=models.CASCADE, null=True,
                            related_name='tube_set')
    strain = models.ForeignKey('Strain', on_delete=models.CASCADE, choices=Strain.objects.all(),
                               related_name='tube_set')
    freeze_group = models.ForeignKey('FreezeGroup', on_delete=models.CASCADE, null=True,
                                     related_name='tube_set')
    thawed = models.BooleanField(default=False)
    thaw_requester = models.CharField(max_length=50, null=True)
    
    def thawed_state(self):
        return 'Thawed' if self.thawed else 'Frozen'
    
    def __repr__(self):
        if self.box:
            location_string = f'Location-JA{self.box.dewar:0>2}-Rack{self.box.rack:0>2}-Box{self.box.box:0>4}'
        else:
            location_string = 'Location-NotStored'
        cap_color_string = f'Cap-{self.cap_color:->6}'

        if not self.thawed:
            return f'Tube(Strain-WJA{self.strain.wja:0>4}, ' \
                   f'{location_string}, {cap_color_string}, ' \
                   f'DateFrozen-{self.date_created.strftime("%m/%d/%Y")})'
        else:
            formatted_thaw_date = self.date_thawed.strftime("%m/%d/%Y") if self.date_thawed else 'N/A'
            return f'ThawedTube(Strain-WJA{self.strain.wja:0>4}, ' \
                   f'{location_string}, {cap_color_string}, ' \
                   f'DateFrozen-{self.date_created.strftime("%m/%d/%Y")}, ' \
                   f'DateThawed-{formatted_thaw_date})'

    def repr(self):
        return self.__repr__()
    
    def __str__(self):
        return self.__repr__()

class Box(models.Model):
    dewar = models.IntegerField()
    rack = models.IntegerField()
    box = models.IntegerField()

    def __repr__(self):
        return f'Box(ID-{self.id:0>6}, Tubes-{self.tube_set.count()})'

    def repr(self):
        return self.__repr__()
    
    def __str__(self):
        return self.__repr__()

class FreezeGroup(models.Model):
    date_created = models.DateField(auto_now_add=True, editable=True)
    date_frozen = models.DateField(null=True)
    strain = models.ForeignKey('Strain', on_delete=models.CASCADE)
    freezer_initials = models.CharField(max_length=15, default='N/A')
    started_test = models.BooleanField(default=False)
    completed_test = models.BooleanField(default=False)
    passed_test = models.BooleanField(default=False)
    tester_initials = models.CharField(max_length=15, null=True)
    tester_comments = models.CharField(max_length=255, null=True)
    test_check_date = models.DateField(null=True)
    stored = models.BooleanField(default=False)

    def __repr__(self):
        return f'FreezeGroup(ID-{self.id:0>6}, Strain-WJA{self.strain.wja}, ' \
               f'Created-{self.date_created.strftime("%m/%d/%Y")})'

    def repr(self):
        return self.__repr__()
    
    def __str__(self):
        return self.__repr__()
