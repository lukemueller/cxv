from Views import contrast_view

class Controller():
    
    def __init__(self, dicom_view, model):
        self.dicom_view = dicom_view
        self.model = model
        self.view = contrast_view.View(self, self.dicom_view, self.model)
