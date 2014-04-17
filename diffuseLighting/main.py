#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''a ripple effect using vertex shader'''


import sys

import PySide
from PySide.QtGui import *
from PySide.QtCore import *
from PySide.QtOpenGL import *

from OpenGL.GL import *
from OpenGL.GL import shaders

import numpy as np

def shaderFromFile(shaderType, shaderFile):
    '''create shader from file'''
    shaderSrc = ''
    with open(shaderFile) as sf:
        shaderSrc = sf.read()
    return shaders.compileShader(shaderSrc, shaderType)


class FreeCamera(object):
    '''a free camera'''
    def __init__(self):
        self.__up = QVector3D(0, 1, 0) # Y axis
        self.__viewDirection = QVector3D(0, 0, -1) # Z axis
        self.__rightAxis = QVector3D() # X axis
        
        # camera position
        self.position = QVector3D()
        self.rotatetion = QVector3D()
        
        # check mouse position
        self.__oldMP = QPoint()
        
        # camera rotate speed
        self.rotateSpeed = .1
        
        self.projection = QMatrix4x4()
        
    def perspective(self, fov, aspect, nearPlane=0.1, farPlane=1000.):
        self.projection.setToIdentity()
        self.projection.perspective(fov, aspect, nearPlane, farPlane)
        
    def getWorldToViewMatrix(self):
        mat = QMatrix4x4()
        mat.lookAt(self.position, self.position + self.__viewDirection, self.__up)
        mat.rotate(self.rotatetion.x(), 1, 0, 0)
        mat.rotate(self.rotatetion.y(), 0, 1, 0)
        mat.rotate(self.rotatetion.z(), 0, 0, 1)
        
        return mat
    
    def updateMouse(self, pos, update=False):
        '''update mouse position and calculate the look direction'''
        if update:
            mouseDelta = pos - self.__oldMP
            
            mat = QMatrix4x4()
            mat.rotate(-mouseDelta.x() * self.rotateSpeed, self.__up)
            
            self.__viewDirection = self.__viewDirection * mat
            self.__rightAxis = QVector3D.crossProduct(self.__viewDirection, self.__up)
            mat.setToIdentity()
            mat.rotate(-mouseDelta.y() * self.rotateSpeed, self.__rightAxis)
            self.__viewDirection = self.__viewDirection * mat
        
        self.__oldMP = pos
        
    def forward(self):
        '''move forward'''
        self.position += self.__viewDirection
    
    def backward(self):
        '''move backward'''
        self.position -= self.__viewDirection
        
    def liftUp(self):
        '''move up'''
        self.position += self.__up
        
    def liftDown(self):
        '''move down'''
        self.position -= self.__up
        
    def strafeLeft(self):
        '''move left'''
        self.position -= self.__rightAxis
        
    def strafeRight(self):
        '''move right'''
        self.position += self.__rightAxis

class Cube(object):
    '''render a cube with triangles'''
    def __init__(self, width=1):
        self._width = 1
        width2 = self._width / 2.0
        
        self.vao = None
        self.vertexVBO = None
        self.normalVBO = None
        self.indexVBO = None
        
        # vertex data
        self.vertex = np.array((
                                # front 
                                (-width2, -width2, width2), 
                                (width2, -width2, width2), 
                                (width2, width2, width2), 
                                (-width2, width2, width2),
                                # right
                                (width2, -width2, width2),
                                (width2, -width2, -width2),
                                (width2, width2, -width2),
                                (width2, width2, width2),
                                # back
                                (-width2, -width2, -width2),
                                (-width2, width2, -width2),
                                (width2, width2, -width2),
                                (width2, -width2, -width2),
                                # left
                                (-width2, -width2, width2),
                                (-width2, width2, width2),
                                (-width2, width2, -width2),
                                (-width2, -width2, -width2),
                                # bottom
                                (-width2, width2, width2),
                                (width2, width2, width2),
                                (width2, width2, -width2),
                                (-width2, width2, -width2),
                                ), dtype=np.float32)
        # normal data
        self.normal = np.array((
                                # front
                                (0, 0, 1),
                                (0, 0, 1),
                                (0, 0, 1),
                                (0, 0, 1),
                                # right
                                (1, 0, 0),
                                (1, 0, 0),
                                (1, 0, 0),
                                (1, 0, 0),
                                # back
                                (0, 0, -1),
                                (0, 0, -1),
                                (0, 0, -1),
                                (0, 0, -1),
                                # left
                                (-1, 0, 0),
                                (-1, 0, 0),
                                (-1, 0, 0),
                                (-1, 0, 0),
                                # bottom
                                (0, -1, 0),
                                (0, -1, 0),
                                (0, -1, 0),
                                (0, -1, 0),
                                # top
                                (0, 1, 0),
                                (0, 1, 0),
                                (0, 1, 0),
                                (0, 1, 0),
                                ), dtype=np.float32)
        self.indices = np.array((0, 1, 2, 
                                 0, 2, 3, 
                                 4, 5, 6, 
                                 4, 6, 7, 
                                 8, 9, 10, 
                                 8, 10, 11, 
                                 12, 13, 14, 
                                 12, 14, 15, 
                                 16, 17, 18, 
                                 16, 18, 19, 
                                 20, 21, 22, 
                                 20, 22, 23,), dtype=np.ushort)
        
        # crate buffers
        self.vao = glGenVertexArrays(0)
        self.vertexVBO, self.indexVBO, self.normalVBO = glGenBuffers(3)
        
        glBindVertexArray(self.vao)
        
        # send vertex data
        glBindBuffer(GL_ARRAY_BUFFER, self.vertexVBO)
        glBufferData(GL_ARRAY_BUFFER, self.vertex.nbytes, self.vertex, GL_STATIC_DRAW)
        
        glEnableVertexAttribArray(0)
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 0, None)
        
        # send normal data
        glBindBuffer(GL_ARRAY_BUFFER, self.normalVBO)
        glBufferData(GL_ARRAY_BUFFER, self.normal.nbytes, self.normal, GL_STATIC_DRAW)
        
        glEnableVertexAttribArray(1)
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 0, None)
        
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.indexVBO)
        glBufferData(GL_ELEMENT_ARRAY_BUFFER, self.indices.nbytes, self.indices, GL_STATIC_DRAW)
        
        glBindVertexArray(0)
    
    def render(self):
        '''draw the cube'''
        glBindVertexArray(self.vao)
        glDrawElements(GL_TRIANGLES, self.indices.size, GL_UNSIGNED_SHORT, None)

class MyGLWidget(QGLWidget):
    
    def __init__(self, gformat, parent=None):
        super(MyGLWidget, self).__init__(gformat, parent)
        
        # buffer object ids
        self.vaoID = None
        self.vboVerticesID = None
        self.vboIndicesID = None
        self.sprogram = None
        
        self.vertices = None
        self.indices = None
        
        # camera
        self.camera = FreeCamera()
        self.state = False
        
        # timer
        self.elapsTimer = QElapsedTimer()
        self.elapsTimer.start()
        self.startTimer(60)
        
        # set window size to the images size
        self.setGeometry(40, 40, 640, 480)
        # set window title
        self.setWindowTitle('ripple effect')
        self.setMouseTracking(True)
        
    def makePlane(self, xsize, zsize, xdivs, zdivs):
        '''make a plane with triangles'''
        vertices = []
        indices = []
        
        # calculate the vertices position
        xs2 = xsize / 2.0
        zs2 = zsize / 2.0
        ifactor = float(zsize) / zdivs
        jfactor = float(xsize) / xdivs
        for i in range(zdivs + 1):
            z = ifactor * i - zs2
            for j in range(xdivs + 1):
                x = jfactor * j - xs2
                pos = (x, 0, z)
                vertices.append(pos)
        
        # vertex indices
        rowStart = 0
        nextRowStart = 0
        for i in range(zdivs):
            rowStart = i * (xdivs + 1)
            nextRowStart = (i + 1) * (xdivs + 1)
            for j in range(xdivs):
                indices.append(rowStart + j)
                indices.append(nextRowStart + j)
                indices.append(nextRowStart + j + 1)
                indices.append(rowStart + j)
                indices.append(nextRowStart + j + 1)
                indices.append(rowStart + j + 1)
                
        return (np.array(vertices, dtype=np.float32), 
                np.array(indices, dtype=np.ushort))
    
    def initializeGL(self):
        glClearColor(0, 0, 0, 0)
        
        # create shader from file
        vshader = shaderFromFile(GL_VERTEX_SHADER, 'shader.vert')
        fshader = shaderFromFile(GL_FRAGMENT_SHADER, 'shader.frag')
        # compile shaders
        self.sprogram = shaders.compileProgram(vshader, fshader)
        
        # get attribute and set uniform for shaders
        glUseProgram(self.sprogram)
        self.vertexAL = glGetAttribLocation(self.sprogram, 'pos')
        self.mvpUL = glGetUniformLocation(self.sprogram, 'MVP')
        self.timeUL = glGetUniformLocation(self.sprogram, 'time')
        glUniform1f(self.timeUL, 0.)
        glUseProgram(0)
        
        # create a grid
        self.vertices, self.indices = self.makePlane(8., 8., 160, 160)
        
        # set up vertex array
        self.vaoID = glGenVertexArrays(1)
        self.vboVerticesID = glGenBuffers(1)
        self.vboIndicesID = glGenBuffers(1)
        
        glBindVertexArray(self.vaoID)
        glBindBuffer(GL_ARRAY_BUFFER, self.vboVerticesID)
        # copy vertices data from memery to gpu memery
        glBufferData(GL_ARRAY_BUFFER, self.vertices.nbytes, self.vertices, GL_STATIC_DRAW)
        # tell opengl how to procces the vertices data
        glEnableVertexAttribArray(self.vertexAL)
        glVertexAttribPointer(self.vertexAL, 3, GL_FLOAT, GL_FALSE, 0, None)
        # send the indice data too
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.vboIndicesID)
        glBufferData(GL_ELEMENT_ARRAY_BUFFER, self.indices.nbytes, self.indices, GL_STATIC_DRAW)
        
        # set camera position
        self.camera.position = QVector3D(0, 0, 5)
        self.camera.rotatetion = QVector3D(30, 35, 0)
        
        # display with wireframe
        glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)
        
        print("Initialization successfull")
        
    def resizeGL(self, w, h):
        glViewport(0, 0, w, h)
        self.camera.perspective(45., float(w) / h)
        
    def paintGL(self):
        # clear the buffers
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        
        time = self.elapsTimer.elapsed() / 1000.
        mvp = self.camera.projection * self.camera.getWorldToViewMatrix()
        mvp = np.array(mvp.copyDataTo(), dtype=np.float32)
        
        # active shader
        glUseProgram(self.sprogram)
        glUniformMatrix4fv(self.mvpUL, 1, GL_TRUE, mvp)
        glUniform1f(self.timeUL, time)
        # draw triangles
        glDrawElements(GL_TRIANGLES, self.indices.size, GL_UNSIGNED_SHORT, None)
        glUseProgram(0)
        
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.state = True
            self.camera.updateMouse(event.pos(), self.state)
    
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.state = False
            self.camera.updateMouse(event.pos(), self.state)
        
    def mouseMoveEvent(self, event):
        pos = event.pos()
        self.camera.updateMouse(pos, self.state)
        self.updateGL()
        
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_W:
            self.camera.forward()
        elif event.key() == Qt.Key_S:
            self.camera.backward()
        elif event.key() == Qt.Key_A:
            self.camera.strafeLeft()
        elif event.key() == Qt.Key_D:
            self.camera.strafeRight()
        elif event.key() == Qt.Key_Q:
            self.camera.liftUp()
        elif event.key() == Qt.Key_Z:
            self.camera.liftDown()
        self.updateGL()
        
    def timerEvent(self, event):
        self.updateGL()


class MyWindow(QMainWindow):
    
    def __init__(self, parent=None):
        super(MyWindow, self).__init__(parent)
        
        self.setWindowTitle('diffuse lighting')
        self.setGeometry(40, 40, 1280, 720)
        
        # setup opengl version and profile
        glformat = QGLFormat()
        glformat.setVersion(4, 3)
        glformat.setProfile(QGLFormat.CoreProfile)
        self.glwidget = MyGLWidget(glformat)
        
        self.setCentralWidget(self.glwidget)
        
    def keyPressEvent(self, event):
        self.glwidget.keyPressEvent(event)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    mywin = MyWindow()
    mywin.show()
    
    # print information on screen
    sys.stdout.write("\tUsing PySide " + PySide.__version__)
    sys.stdout.write("\n\tVendor: " + glGetString(GL_VENDOR))
    sys.stdout.write("\n\tRenderer: " + glGetString(GL_RENDERER))
    sys.stdout.write("\n\tVersion: " + glGetString(GL_VERSION))
    sys.stdout.write("\n\tGLSL: " + glGetString(GL_SHADING_LANGUAGE_VERSION))
    
    sys.exit(app.exec_())
