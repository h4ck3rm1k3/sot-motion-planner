
glMaterialfv(GL_FRONT_AND_BACK,  GL_AMBIENT_AND_DIFFUSE, [0,0,1,1])
glMaterialfv(GL_FRONT_AND_BACK,  GL_SPECULAR           , [0,0,1,1])
glMaterialfv(GL_FRONT_AND_BACK,  GL_EMISSION           , [0,0,1,1])
glMaterialf(GL_FRONT_AND_BACK, GL_SHININESS, 6)
glBegin(GL_LINES)
glVertex3f(0.0, 0.0, 0.0); glVertex3f(0.1, 0.0, 0.0)
glEnd()

glMaterialfv(GL_FRONT_AND_BACK,  GL_AMBIENT_AND_DIFFUSE, [1,0,0,1])
glMaterialfv(GL_FRONT_AND_BACK,  GL_SPECULAR           , [1,0,0,1])
glMaterialfv(GL_FRONT_AND_BACK,  GL_EMISSION           , [1,0,0,1])
glMaterialf(GL_FRONT_AND_BACK, GL_SHININESS, 6)
glBegin(GL_LINES)
glVertex3f(0.0, 0.0, 0.0); glVertex3f(0.0, 0.1, 0.0)
glVertex3f(0.0, 0.0, 0.0); glVertex3f(0.0, 0.0, 0.1)
glEnd()

glMaterialfv(GL_FRONT_AND_BACK,  GL_AMBIENT_AND_DIFFUSE, [0,1,0,1])
glMaterialfv(GL_FRONT_AND_BACK,  GL_SPECULAR           , [0,1,0,1])
glMaterialfv(GL_FRONT_AND_BACK,  GL_EMISSION           , [0,1,0,1])
glMaterialf(GL_FRONT_AND_BACK, GL_SHININESS, 6)
glBegin(GL_LINES)
glVertex3f(0.0, 0.0, 0.0); glVertex3f(0.0, 0.0, 0.1)
glEnd()
