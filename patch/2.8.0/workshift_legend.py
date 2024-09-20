from irhrs.attendance.models import WorkShiftLegend, WorkShift

WorkShiftLegend.objects.bulk_create([
    WorkShiftLegend(
        shift=ws,
        legend_text=ws.name[:2].upper(),
        legend_color="#9E9E9EFF"
    ) for ws in WorkShift.objects.filter(work_shift_legend__isnull=True)
])
