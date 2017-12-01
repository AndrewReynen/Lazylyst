import sys
from PyQt5.QtWidgets import QTreeWidget, QTreeWidgetItem, QApplication, QWidget,QMenu, QComboBox
from PyQt5.QtCore import Qt,QPoint



class MyTreeWidget(QTreeWidget):
    def __init__(self, parent = None):
        QTreeWidget.__init__(self, parent)
    def mousePressEvent (self, event):
        # Do nothing if no item was clicked
        if self.itemAt(event.pos()) is None:
            self.clearSelection()
            return
        # Otherwise set the current item to be the selected item
        else:
            self.setCurrentItem(self.itemAt(event.pos()))
            
        # Pop up menu if 
        if event.button() == Qt.RightButton and self.currentItem().parent() is None:
            self.create_popup_menu(event)
        elif self.currentItem().parent() is not None:
            if self.currentItem().parent().parent() is None:
                print 1
        QTreeWidget.mousePressEvent(self, event)
        
    def new_cluster(self):
        print "New Cluster"
        self.addTopLevelItem(QTreeWidgetItem(["String A", "String B", "String AAA"]))
    
    def rename_cluster(self):
        print "Rename cluster"
        self.currentItem().setText(0,'haha')
    
    def delete_cluster(self):
        print "Delete cluster"
    
    def create_popup_menu(self,event, parent=None):
#        print event.pos()
        self.popup_menu = QMenu(parent)
        self.popup_menu.addAction("New", self.new_cluster)
        self.popup_menu.addAction("Rename", self.rename_cluster)
        self.popup_menu.addSeparator()
        self.popup_menu.addAction("Delete", self.delete_cluster)
        self.popup_menu.move(self.mapToGlobal(QPoint(0,0))+event.pos())
        self.popup_menu.show() 

if __name__ == '__main__':
    
    app = 0
    if QApplication.instance():
        app = QApplication.instance()
    else:
        app = QApplication(sys.argv)
        
    c1=QComboBox()
    
    l1 = QTreeWidgetItem(["String A", "String B", "String C"])
    l2 = QTreeWidgetItem(["String AA", "String BB", "String CC"])
    for i in range(3):
        l1_child = QTreeWidgetItem(["Child A" + str(i), "Child B" + str(i), "Child C" + str(i)])
        
        l1.addChild(l1_child)

    for j in range(2):
        l2_child = QTreeWidgetItem(["Child AA" + str(j), "Child BB" + str(j), "Child CC" + str(j)])
        l2.addChild(l2_child)
        

    w = QWidget()
    w.resize(510, 210)

    tw = MyTreeWidget(w)
    
    tw.resize(500, 200)
    tw.setColumnCount(3)
    tw.setHeaderLabels(["Column 1", "Column 2", "Column 3"])
    tw.addTopLevelItem(l1)
    tw.addTopLevelItem(l2)
    tw.setItemWidget(l2_child,1,c1)
    c1.addItems(['hehe','haha','teeheee'])

    w.show()
    sys.exit(app.exec_())
    
    