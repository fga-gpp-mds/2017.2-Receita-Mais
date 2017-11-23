# Standard
from io import BytesIO

# Django
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator

# Local Django imports
from user.decorators import is_health_professional
from prescription.models import Prescription, Pattern
from prescription.views import NumberedCanvas

# Third-Party
from reportlab.lib.pagesizes import letter, A4, A5
from reportlab.pdfgen import canvas
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, PageTemplate, Frame
from reportlab.lib.colors import (black, purple, white, yellow)
from reportlab.lib.units import inch, mm
from reportlab.lib.utils import ImageReader


class PrintPrescription:

    def __init__(self, buffer, prescription, pattern):
        self.buffer = buffer
        self.prescription = prescription
        self.pattern = pattern
        self.width = pattern.pagesize
        self.height = pattern.pagesize
        if pattern.pagesize == 'A4':
            self.pagesize = A4
        elif pattern.pagesize == 'A5':
            self.pagesize = A5
        elif pattern.pagesize == 'letter':
            self.pagesize = letter


    def _header_footer(self, canvas, doc):
        # Save the state of our canvas so we can draw on it
        canvas.saveState()
        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(name='centered', alignment=TA_CENTER))
        styles.add(ParagraphStyle(name='right', alignment=TA_RIGHT))
        # Header
        header = Paragraph(self.pattern.header, styles['right'])
        w, h = header.wrap(doc.width, doc.topMargin)
        header.drawOn(canvas, doc.leftMargin, doc.height + doc.topMargin - h)

        # Footer
        footer = Paragraph(self.pattern.footer, styles['centered'])
        w, h = footer.wrap(doc.width, doc.bottomMargin)
        footer.drawOn(canvas, doc.leftMargin, h)
        if self.pagesize == A4:
            canvas.setLineWidth(0.5)
            canvas.line(66, 78, letter[0] - 66, 78)
            canvas.setLineWidth(.3)
            canvas.line(30, 750, 580, 750)
            if self.pattern.logo:
                img = ImageReader(self.pattern.logo.path)
                canvas.drawImage(img, 30, 730, 0.75 * inch, 0.75 * inch, mask='auto')

        elif self.pagesize == A5:
            canvas.setLineWidth(0.5)
            canvas.line(66, 78, A5[0] - 66, 78)
            canvas.setLineWidth(.3)
            canvas.line(30, 500, 390, 500)
            if self.pattern.logo:
                img = ImageReader(self.pattern.logo.path)
                canvas.drawImage(img, 30, 510, 0.75 * inch, 0.75 * inch, mask='auto')

        elif self.pagesize == letter:
            canvas.setLineWidth(0.5)
            canvas.line(66, 78, letter[0] - 66, 78)
            canvas.setLineWidth(.3)
            canvas.line(30, 700, 580, 700)
            if self.pattern.logo:
                img = ImageReader(self.pattern.logo.path)
                canvas.drawImage(img, 30, 730, 0.75*inch, 0.75*inch, mask='auto')

        # Release the canvas
        canvas.restoreState()

    def print_users(self):
        prescription = self.prescription
        pattern = self.pattern
        buffer = self.buffer

        if self.pagesize == A4:
            doc = SimpleDocTemplate(buffer,
                                    rightMargin=100,
                                    leftMargin=100,
                                    topMargin=50,
                                    bottomMargin=50,
                                    pagesize=self.pagesize)

        elif self.pagesize == A5:
            doc = SimpleDocTemplate(buffer,
                                    rightMargin=50,
                                    leftMargin=50,
                                    topMargin=50,
                                    bottomMargin=50,
                                    pagesize=self.pagesize)

        elif self.pagesize == letter:
            doc = SimpleDocTemplate(buffer,
                                    rightMargin=100,
                                    leftMargin=100,
                                    topMargin=50,
                                    bottomMargin=50,
                                    pagesize=self.pagesize)

        elements = []

        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(name='centered', alignment=TA_CENTER))
        styles.add(ParagraphStyle(
                'default',
                fontName=pattern.font,
                fontSize=int(pattern.font_size),
                leading=12,
                leftIndent=0,
                rightIndent=0,
                firstLineIndent=0,
                alignment=TA_LEFT,
                spaceBefore=0,
                spaceAfter=0,
                bulletFontName=pattern.font,
                bulletFontSize=int(pattern.font_size),
                bulletIndent=0,
                textColor=black,
                backColor=None,
                wordWrap=None,
                borderWidth=0,
                borderPadding=0,
                borderColor=None,
                borderRadius=None,
                allowWidows=1,
                allowOrphans=0,
                textTransform=None,  # 'uppercase' | 'lowercase' | None
                endDots=None,
                splitLongWords=1,)
        )

        # Draw things on the PDF. Here's where the PDF generation happens.
        elements.append(Spacer(1, 50))

        if len(prescription.medicines.all()) != 0 or prescription.manipulated_medicines.all() != 0:
            elements.append(Paragraph('Medicamentos', styles['Heading1']))
            for medicine in prescription.medicines.all():
                elements.append(Paragraph(medicine.name, styles['default']))

                for prescription_medicine in prescription.prescriptionhasmedicine_set.all():
                    if prescription_medicine.medicine == medicine:
                        elements.append(Paragraph(prescription_medicine.via, styles['default']))
                        elements.append(Paragraph(prescription_medicine.posology, styles['default']))
                        elements.append(Paragraph(prescription_medicine.get_quantity_display(), styles['default']))
                elements.append(Spacer(1, 12))

            for custom_medicine in prescription.manipulated_medicines.all():
                elements.append(Paragraph(custom_medicine.recipe_name, styles['default']))

                for custom_prescription_medicine in prescription.prescriptionhasmanipulatedmedicine_set.all():
                    if custom_prescription_medicine.manipulated_medicine == custom_medicine:
                        elements.append(Paragraph(custom_prescription_medicine.via, styles['default']))
                        elements.append(Paragraph(custom_prescription_medicine.posology, styles['default']))
                        elements.append(Paragraph(custom_prescription_medicine.get_quantity_display(), styles['default']))
                elements.append(Spacer(1, 12))
        else:
            # Nothing to do.
            pass

        elements.append(Spacer(1, 12))
        if len(prescription.recommendation_prescription.all()) != 0:
            elements.append(Paragraph('Recomendacoes', styles['Heading1']))
            for recommendation in prescription.recommendation_prescription.all():
                elements.append(Paragraph(recommendation.recommendation, styles['default']))
                elements.append(Spacer(1, 12))
        else:
            # Nothing to do.
            pass

        elements.append(Spacer(1, 12))
        if len(prescription.default_exams.all()) != 0 or len(prescription.custom_exams.all()) != 0:
            elements.append(Paragraph('Exames', styles['Heading1']))
            for default_exams in prescription.default_exams.all():
                elements.append(Paragraph(default_exams.description, styles['default']))
                elements.append(Spacer(1, 12))

            for custom_exams in prescription.custom_exams.all():
                elements.append(Paragraph(custom_exams.description, styles['default']))
                elements.append(Spacer(1, 12))

        else:
            # NOTHING TO DO
            pass

        doc.build(elements, onFirstPage=self._header_footer, onLaterPages=self._header_footer,
                  canvasmaker=NumberedCanvas)

        # Get the value of the BytesIO buffer and write it to the response.
        pdf = buffer.getvalue()
        buffer.close()
        return pdf

    def generate_pdf(request, pk, jk):
        # Create the HttpResponse object with the appropriate PDF headers.
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="My Users.pdf"'
        prescription = Prescription.objects.get(pk=pk)
        pattern = Pattern.objects.get(pk=jk)
        buffer = BytesIO()

        report = PrintPrescription(buffer, prescription, pattern)
        pdf = report.print_users()

        response.write(pdf)
        return response
