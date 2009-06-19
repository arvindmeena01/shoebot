
class OldBot:
    '''
    The Box class is an abstraction to hold a Cairo surface, context and all
    methods to access and manipulate it (the Nodebox language is
    implemented here).
    '''

    inch = 72
    cm = 28.3465
    mm = 2.8346

    RGB = "rgb"
    HSB = "hsb"

    NORMAL = "1"
    FORTYFIVE = "2"

    CENTER = "center"
    CORNER = "corner"
    CORNERS = "corners"

    DEFAULT_WIDTH = 200
    DEFAULT_HEIGHT = 200

    def __init__ (self, inputscript=None, gtkmode=False, outputfile = None):

        self.inputscript = inputscript
        self.targetfilename = outputfile
        # create options object
        self.opt = OptionsContainer()
        # init internal path container
        self._path = None
        self._autoclosepath = True
        # init temp value holders
        self._fill = None
        self._stroke = None

        self.context = None
        self.surface = None

        self.gtkmode = gtkmode
        self.vars = []
        self._oldvars = self.vars
        self.namespace = {}

        self.WIDTH = Box.DEFAULT_WIDTH
        self.HEIGHT = Box.DEFAULT_HEIGHT

    def setsurface(self, width=None, height=None, target=None):
        '''Sets the surface on which the Box object will operate.

        Besides attaching surfaces, it can also create new ones based on an
        output filename; it also accepts a Cairo surface or context as an
        argument, and attaches to them as expected.
        '''

        if not width:
            width = self.WIDTH
        if not height:
            height = self.HEIGHT

        if not target:
            raise ShoebotError(_("setsurface(): No target specified!"))
        if isinstance(target, basestring):
            # if the target is a string, should be a filename
            filename = target
            self.surface = util.surfacefromfilename(filename,width,height)
            self.context = cairo.Context(self.surface)
        elif isinstance(target, cairo.Surface):
            # and if it's a surface, attach our Cairo context to it
            self.surface = target
            self.context = cairo.Context(target)
        elif isinstance(target, cairo.Context):
            # if it's a Cairo context, use it instead of making a new one
            self.context = target
            self.surface = self.context.get_target()
        else:
            raise ShoebotError(_("setsurface: Argument must be a file name, a Cairo surface or a Cairo context"))

    def get_context(self):
        return self.context
    def get_surface(self):
        return self.surface

    #### Drawing

    def rect(self, x, y, width, height, roundness=0.0, fill=None, stroke=None):
        '''Draws a rectangle with top left corner at (x,y)

        The roundness variable sets rounded corners.
        '''
        # taken from Nodebox and modified

        if self.opt.rectmode == self.CORNERS:
            width = width - x
            height = height - y
        elif self.opt.rectmode == self.CENTER:
            x = x - width / 2
            y = y - height / 2
        elif self.opt.rectmode == self.CORNER:
            pass

        # take care of fill and stroke arguments
        if fill is not None or stroke is not None:
            if fill is not None:
                self._fill = self.color(fill)
            if stroke is not None:
                self._stroke = self.color(stroke)

        # straight corners
        if roundness == 0.0:
            self.context.rectangle(x, y, width, height)
            self.fill_and_stroke()
        # rounded corners
        else:
            curve = min(width*roundness, height*roundness)
            self.beginpath()
            self.moveto(x, y+curve)
            self.curveto(x, y, x, y, x+curve, y)
            self.lineto(x+width-curve, y)
            self.curveto(x+width, y, x+width, y, x+width, y+curve)
            self.lineto(x+width, y+height-curve)
            self.curveto(x+width, y+height, x+width, y+height, x+width-curve, y+height)
            self.lineto(x+curve, y+height)
            self.curveto(x, y+height, x, y+height, x, y+height-curve)
            self.endpath()

        # revert to previous fill/stroke values if arguments were specified
        if fill is not None or stroke is not None:
            self._fill = None
            self._stroke = None

    def rectmode(self, mode=None):
        if mode in (self.CORNER, self.CENTER, self.CORNERS):
            self.opt.rectmode = mode
            return self.opt.rectmode
        elif mode is None:
            return self.opt.rectmode
        else:
            raise ShoebotError(_("rectmode: invalid input"))

    def oval(self, x, y, width, height):
        '''Draws an ellipse starting from (x,y)'''

        self.context.save()
        self.context.translate (x + width / 2., y + height / 2.);
        self.scale (width / 2., height / 2.);
        self.arc (0., 0., 1., 0., 2 * pi);
        self.fill_and_stroke()
        self.context.restore()

    def circle(self, x, y, diameter):
        self.oval(x, y, diameter, diameter)


    def line(self, x1, y1, x2, y2):
        '''Draws a line from (x1,y1) to (x2,y2)'''
        self.beginpath()
        self.moveto(x1,y1)
        self.lineto(x2,y2)
        self.endpath()

    def arrow(self, x, y, width, type=NORMAL):
        '''Draws an arrow.

        Arrows can be two types: NORMAL or FORTYFIVE.
        Taken from Nodebox.
        '''
        if type == self.NORMAL:
            head = width * .4
            tail = width * .2
            self.beginpath()
            self.moveto(x, y)
            self.lineto(x-head, y+head)
            self.lineto(x-head, y+tail)
            self.lineto(x-width, y+tail)
            self.lineto(x-width, y-tail)
            self.lineto(x-head, y-tail)
            self.lineto(x-head, y-head)
            self.lineto(x, y)
            self.endpath()
#            self.fill_and_stroke()
        elif type == self.FORTYFIVE:
            head = .3
            tail = 1 + head
            self.beginpath()
            self.moveto(x, y)
            self.lineto(x, y+width*(1-head))
            self.lineto(x-width*head, y+width)
            self.lineto(x-width*head, y+width*tail*.4)
            self.lineto(x-width*tail*.6, y+width)
            self.lineto(x-width, y+width*tail*.6)
            self.lineto(x-width*tail*.4, y+width*head)
            self.lineto(x-width, y+width*head)
            self.lineto(x-width*(1-head), y)
            self.lineto(x, y)
            self.endpath()
#            self.fill_and_stroke()
        else:
            raise NameError(_("arrow: available types for arrow() are NORMAL and FORTYFIVE\n"))

    def star(self, startx, starty, points=20, outer=100, inner=50):
        '''Draws a star.

        Taken from Nodebox.
        '''
        self.beginpath()
        self.moveto(startx, starty + outer)

        for i in range(1, int(2 * points)):
            angle = i * pi / points
            x = sin(angle)
            y = cos(angle)
            if i % 2:
                radius = inner
            else:
                radius = outer
            x = startx + radius * x
            y = starty + radius * y
            self.lineto(x,y)

        self.endpath()
#        self.fill_and_stroke()


    # ----- PATH -----
    # Path functions taken from Nodebox and modified

    def beginpath(self, x=None, y=None):
        # create a BezierPath instance
        ## FIXME: This is fishy
        self._path = BezierPath((x,y))
        self._path.closed = False

        # if we have arguments, do a moveto too
        if x is not None and y is not None:
            self._path.moveto(x,y)

    def moveto(self, x, y):
        if self._path is None:
            ## self.beginpath()
            raise ShoebotError, _("No current path. Use beginpath() first.")
        self._path.moveto(x,y)

    def lineto(self, x, y):
        if self._path is None:
            raise ShoebotError, _("No current path. Use beginpath() first.")
        self._path.lineto(x, y)

    def curveto(self, x1, y1, x2, y2, x3, y3):
        if self._path is None:
            raise ShoebotError, _("No current path. Use beginpath() first.")
        self._path.curveto(x1, y1, x2, y2, x3, y3)

    def closepath(self):
        if self._path is None:
            raise ShoebotError, _("No current path. Use beginpath() first.")
        if not self._path.closed:
            self._path.closepath()
            self._path.closed = True

    def endpath(self, draw=True):
        if self._path is None:
            raise ShoebotError, _("No current path. Use beginpath() first.")
        if self._autoclosepath:
            self._path.closepath()
        p = self._path
        if draw:
            self.drawpath(p)
        self._path = None
        return p

    def drawpath(self,path):
        if not isinstance(path, BezierPath):
            raise ShoebotError, _("drawpath(): Input is not a valid BezierPath object")
        self.context.save()
        for element in path.data:
            if not isinstance(element,PathElement):
                raise ShoebotError(_("drawpath(): Path is not properly constructed (expecting a path element, got ") + element + ")")

            cmd = element[0]

            if cmd == MOVETO:
                x = element.x
                y = element.y
                self.context.move_to(x, y)
            elif cmd == LINETO:
                x = element.x
                y = element.y
                self.context.line_to(x, y)
            elif cmd == CURVETO:
                c1x = element.c1x
                c1y = element.c1y
                c2x = element.c2x
                c2y = element.c2y
                x = element.x
                y = element.y
                self.context.curve_to(c1x, c1y, c2x, c2y, x, y)
            elif cmd == CLOSE:
                self.context.close_path()
            else:
                raise ShoebotError(_("PathElement(): error parsing path element command (got '%s')") % (cmd))
        ## TODO
        ## if path has state attributes, set the context to those, saving
        ## before and replacing them afterwards with the old values
        ## else, just go on
        # if path.stateattrs:
        #     for attr in path.stateattrs:
        #         self.context....

        self.fill_and_stroke()
        self.context.restore()

    def autoclosepath(self, close=True):
        self._autoclosepath = close

    def relmoveto(self, x, y):
        '''Move relatively to the last point.

        Calls Cairo's rel_move_to().
        '''
        self.context.rel_move_to(x,y)
    def rellineto(self, x,y):
        '''Draws a line relatively to the last point.

        Calls Cairo's rel_line_to().
        '''
        self.context.rel_line_to(x,y)

    def relcurveto(self, h1x, h1y, h2x, h2y, x, y):
        '''Draws a curve relatively to the last point.

        Calls Cairo's rel_curve_to().
        '''
        self.context.rel_curve_to(h1x, h1y, h2x, h2y, x, y)

    def arc(self,centerx, centery, radius, angle1, angle2):
        '''Draws an arc.

        Calls Cairo's arc() method.
        '''
        self.context.arc(centerx, centery, radius, angle1, angle2)

    def findpath(self, list, curvature=1.0):
        ''' (NOT IMPLEMENTED) Builds a path from a list of point coordinates.
        Curvature: 0=straight lines 1=smooth curves
        '''
        raise NotImplementedError(_("findpath() isn't implemented yet (sorry)"))
        #import bezier
        #path = bezier.findpath(points, curvature=curvature)
        #path.ctx = self
        #path.inheritFromContext()
        #return path

    #### Transform and utility

    def beginclip(self,x,y,w,h):
        self.save()
        self.context.rectangle(x, y, w, h)
        self.context.clip()

    def endclip(self):
        self.restore()

    def transform(self, mode=CENTER): # Mode can be CENTER or CORNER
        '''
        NOT IMPLEMENTED
        '''
        raise NotImplementedError(_("transform() isn't implemented yet"))

    def apply_matrix(self, xx=1.0, yx=0.0, xy=0.0, yy=1.0, x0=0.0, y0=0.0):
        '''
        Adds mtrx to the current transformation matrix
        '''
        mtrx = cairo.Matrix(xx, yx, xy, yy, x0, y0)
        try:
            self.context.transform(mtrx)
        except cairo.Error:
            print "Invalid transformation matrix (%2f,%2f,%2f,%2f,%2f,%2f)" % (xx, yx, xy, yy, x0, y0)

    def translate(self, x, y):
        '''
        Shifts the origin point by (x,y)
        '''
        # self.context.translate(x, y)
        self.apply_matrix(1,0,0,1,x,y)

    def rotate(self, degrees=0, radians=0):
        if degrees:
            a = deg2rad(degrees)
        else:
            a = radians
        # self.context.rotate(a)
        self.apply_matrix(cos(a), sin(a), -sin(a), cos(a), 0, 0)

    def scale(self, x=1, y=None):
        if x == 0 or y == 0:
            print _("Scale parameters can't be 0. Ignoring")
            return
        y = x
        # self.context.scale(x,y)
        self.apply_matrix(x,0,0,y,0,0)

    def skew(self, x=1, y=None):
        self.apply_matrix(1,0,x,1,0,0)
        if y:
            self.apply_matrix(1,y,0,1,0,0)

    def save(self):
        #self.push_group()
        self.context.save()

    def restore(self):
        #self.pop_group()
        self.context.restore()

    def push(self):
        #self.push_group()
        self.context.save()

    def pop(self):
        #self.pop_group()
        self.context.restore()

    def reset(self):
        self.context.identity_matrix()

    #### Color

    def outputmode(self):
        '''
        NOT IMPLEMENTED
        '''
        raise NotImplementedError(_("outputmode() isn't implemented yet"))

    def colormode(self, mode=None, crange=None):
        '''Sets the current colormode (can be RGB or HSB) and eventually
        the color range.

        If called without arguments, it returns the current colormode.
        '''
        if mode is not None:
            if mode == "rgb":
                self.opt.color_mode = RGB
            elif mode == "hsb":
                self.opt.color_mode = HSB
            else:
                raise NameError, _("Only RGB and HSB colormodes are supported.")
        if crange is not None:
            self.opt.color_range = crange
        return self.opt.color_mode

    def color(self,*args):
        if isinstance(args[0], Color):
            return Color(args[0], mode=RGB, color_range=1)
        else:
            return Color(args, box=self)

    def colorrange(self, crange):
        self.opt.color_range = float(crange)

    def fill(self,*args):
        '''Sets a fill color, applying it to new paths.'''
        self.opt.fillapply = True
        self.opt.fillcolor = self.color(*args)
        return self.opt.fillcolor

    def nofill(self):
        ''' Stops applying fills to new paths.'''
        self.opt.fillapply = False

    def stroke(self,*args):
        '''Sets a stroke color, applying it to new paths.'''
        self.opt.strokeapply = True
        self.opt.strokecolor = self.color(*args)
        return self.opt.strokecolor

    def nostroke(self):
        ''' Stops applying strokes to new paths.'''
        self.opt.strokeapply = False

    def strokewidth(self, w=None):
        '''Sets the stroke width.'''
        if w is not None:
            self.context.set_line_width(w)
        else:
            return self.context.get_line_width

    def background(self,*args):
        '''Sets the background colour.'''

        bg = self.color(*args)
        self.context.set_source_rgb(bg.r, bg.g, bg.b)
        self.context.paint()

    #### Text

    def font(self, fontpath=None, fontsize=None):
        '''Set the font to be used with new text instances.

        Accepts TrueType and OpenType files. Depends on FreeType being
        installed.'''
        if fontpath is not None:
            face = util.create_cairo_font_face_for_file(fontpath, 0)
            self.context.set_font_face(face)
        else:
            self.context.get_font_face()
        if fontsize is not None:
            self.fontsize(fontsize)

    def fontsize(self, fontsize=None):
        if fontsize is not None:
            self.context.set_font_size(fontsize)
        else:
            return self.context.get_font_size()

    def text(self, txt, x, y, width=None, height=1000000, outline=False):
        '''
        Draws a string of text according to current font settings.
        '''
        # TODO: Check for malformed requests (x,y,txt is a common mistake)
        self.save()
        if width is not None:
            pass
        if outline is True:
            self.textpath(txt, x, y, width, height)
        else:
            self.context.move_to(x,y)
            self.context.show_text(txt)
            self.fill_and_stroke()
        self.restore()

    def textpath(self, txt, x, y, width=None, height=1000000, draw=True):
        '''
        Draws an outlined path of the input text
        '''
        ## FIXME: This should be handled by BezierPath
        self.save()
        self.context.move_to(x,y)
        self.context.text_path(txt)
        self.restore()
#        return self._path

    def textwidth(self, txt, width=None):
        '''Returns the width of a string of text according to the current
        font settings.
        '''
        return textmetrics(txt)[0]

    def textheight(self, txt, width=None):
        '''Returns the height of a string of text according to the current
        font settings.
        '''
        return textmetrics(txt)[1]

    def textmetrics(self, txt, width=None):
        '''Returns the width and height of a string of text as a tuple
        (according to current font settings).
        '''
        # for now only returns width and height (as per Nodebox behaviour)
        # but maybe we could use the other data from cairo
        x_bearing, y_bearing, textwidth, textheight, x_advance, y_advance = self.context.text_extents(txt)
        return textwidth, textheight

    def lineheight(self, height=None):
        '''
        NOT IMPLEMENTED
        '''
        # default: 1.2
        # sets leading
        raise NotImplementedError(_("lineheight() isn't implemented yet"))

    def align(self, align="LEFT"):
        '''
        NOT IMPLEMENTED
        '''
        # sets alignment to LEFT, RIGHT, CENTER or JUSTIFY
        raise NotImplementedError(_("align() isn't implemented in Shoebot yet"))

    # TODO: Set the framework to setup font options

    def fontoptions(self, hintstyle=None, hintmetrics=None, subpixelorder=None, antialias=None):
        raise NotImplementedError(_("fontoptions() isn't implemented yet"))

    # ----- IMAGE -----

    def image(self, path, x, y, width=None, height=None, alpha=1.0, data=None):
        '''
        TODO:
        width and height ought to be for scaling, not clipping
        Use gdk.pixbuf to load an image buffer and convert it to a cairo surface
        using PIL
        '''
        #width, height = im.size
        imagesurface = cairo.ImageSurface.create_from_png(path)
        self.context.set_source_surface (imagesurface, x, y)
        self.context.rectangle(x, y, width, height)
        self.context.fill()

    #### Variables

    def var(self, name, type, default=None, min=0, max=100, value=None):
        v = Variable(name, type, default, min, max, value)
        v = self.addvar(v)

    def addvar(self, v):
        ''' Sets a new accessible variable.'''

        oldvar = self.findvar(v.name)
        if oldvar is not None:
            if oldvar.compliesTo(v):
                v.value = oldvar.value
        self.vars.append(v)
        self.namespace[v.name] = v.value

    def findvar(self, name):
        for v in self._oldvars:
            if v.name == name:
                return v
        return None

    def setvars(self,args):
        '''Defines the variables that can be externally set.

        Accepts a dictionary with variable names assigned
        to default values. If called more than once, it updates
        already existing values and adds new keys to accomodate
        new entries.

        DEPRECATED, use addvar() instead
        '''
        if not isinstance(args, dict):
            raise ShoebotError(_('setvars(): setvars needs a dict!'))
        vardict = args
        for item in vardict:
            self.var(item, NUMBER, vardict[item])

    #### Utility

    def random(self,v1=None, v2=None):
        # ipsis verbis from Nodebox
        if v1 is not None and v2 is None:
            if isinstance(v1, float):
                return random.random() * v1
            else:
                return int(random.random() * v1)
        elif v1 != None and v2 != None:
            if isinstance(v1, float) or isinstance(v2, float):
                start = min(v1, v2)
                end = max(v1, v2)
                return start + random.random() * (end-start)
            else:
                start = min(v1, v2)
                end = max(v1, v2) + 1
                return int(start + random.random() * (end-start))
        else: # No values means 0.0 -> 1.0
            return random.random()

    def grid(self, cols, rows, colSize=1, rowSize=1, shuffled = False):
        """Returns an iterator that contains coordinate tuples.
        The grid can be used to quickly create grid-like structures.
        A common way to use them is:
            for x, y in grid(10,10,12,12):
                rect(x,y, 10,10)
        """
        # Taken ipsis verbis from Nodebox

        rowRange = range(int(rows))
        colRange = range(int(cols))
        if (shuffled):
            shuffle(rowRange)
            shuffle(colRange)
        for y in rowRange:
            for x in colRange:
                yield (x*colSize,y*rowSize)

    def files(self, path="*"):
        """Returns a list of files.
        You can use wildcards to specify which files to pick, e.g.
            f = files('*.gif')
        """
        # Taken ipsis verbis from Nodebox
        return glob(path)

    def snapshot(self,filename=None, surface=None):
        '''Save the contents of current surface into a file.

        There's two uses for this method:
        - called from a script to create a output file
        - called from the Shoebot window menu, which requires the source surface
        to be specified in the arguments.

        - if output is bitmap (PNG, GTK), then it clones current surface via
          Cairo
        - if output is vector, doing the source paint in Cairo ends up in a
          vector file with an embedded bitmap - not good. So we just create
          another Box instance with the currently loaded script, copy the
          current namespace and save its output in a file.

        The shortcomings of this is that
        '''

        f, ext = os.path.splitext(filename)

        if ext == "png":
            # bitmap snapshots can be done via Cairo
            if isinstance(self.surface, cairo.ImageSurface):
                # if current surface is a bitmap image surface, we can write the
                # file right away
                self.surface.write_to_png(filename)
            else:
                # otherwise, we clone the contents of current surface onto
                # a temporary one
                temp_surface = util.surfacefromfilename(filename, self.WIDTH, self.HEIGHT)
                ctx = cairo.Context(temp_surface)
                ctx.set_source_surface(self.surface, 0, 0)
                ctx.paint()
                temp_surface.write_to_png(filename)
                del temp_surface

        if ext in (".svg",".ps",".pdf"):
            # vector snapshots are made with another temporary Box

            # create a Box instance using the current running script
            box = Box(inputscript=self.inputscript, outputfile=filename)
            box.run()

            # FIXME: This approach makes random values/values generated at
            # start be re-calculated once a script runs again :/
            #
            # this will have to do until we have a proper Canvas class
            # which would register all objects before passing it to the
            # Cairo context

            # set its variables to the current ones
            for v in self.vars:
                box.namespace[v.name] = self.namespace[v.name]
            if 'setup' in box.namespace:
                box.namespace['setup']()
            if 'draw' in box.namespace:
                box.namespace['draw']()
            box.finish()
            print _(_("Saved snapshot to %s")) % filename
            del box

    #### Core functions

    def size(self,w=None,h=None):
        '''Sets the size of the canvas, and creates a Cairo surface and context.

        Needs to be the first function call in a script.'''

        if not w:
            w = self.WIDTH
        if not h:
            h = self.HEIGHT

        if self.gtkmode:
            # in windowed mode we don't set the surface in the Box itself,
            # the gtkui module takes care of doing that
            # TODO: Parent widget as an argument?
            self.WIDTH = int(w)
            self.HEIGHT = int(h)
            self.namespace['WIDTH'] = self.WIDTH
            self.namespace['HEIGHT'] = self.HEIGHT

        else:
            self.WIDTH = int(w)
            self.HEIGHT = int(h)
            # hack to get WIDTH and HEIGHT into the local namespace for running
            self.namespace['WIDTH'] = self.WIDTH
            self.namespace['HEIGHT'] = self.HEIGHT
            # make a new surface for us
            self.setsurface(w, h, self.targetfilename)
        # return (self.WIDTH, self.HEIGHT)

    def fill_and_stroke(self):
        '''
        Apply fill and stroke settings, and apply the current path to the final surface.
        '''
        if DEBUG: print "DEBUG: Beginning fill_and_stroke()"
        # we need to give cairo values between 0-1
        # and for that we need to make a special request to Color()
        if self._fill is not None:
            fillclr = self._fill
        else:
            fillclr = self.opt.fillcolor

        if self._stroke is not None:
            strokeclr = self._stroke
        else:
            strokeclr = self.opt.strokecolor

        self.context.save()
        if self.opt.fillapply is True:
            self.context.set_source_rgba(fillclr[0],fillclr[1],fillclr[2],fillclr[3])
            if self.opt.strokeapply is True:
                # if there's a stroke still to be applied, we need to call fill_preserve()
                # which still leaves this path as active
                self.context.fill_preserve()
                self.context.set_source_rgba(strokeclr[0],strokeclr[1],strokeclr[2],strokeclr[3])
                # now apply the stroke (stroke ends the path, we'd use stroke_preserve()
                # for further operations if needed)
                self.context.stroke()
            else:
                # if there isn't a stroke, use plain fill() to close the path
                self.context.fill()
        elif self.opt.strokeapply is True:
            # if there's no fill, apply stroke only
            self.context.set_source_rgba(strokeclr[0],strokeclr[1],strokeclr[2],strokeclr[3])
            self.context.stroke()
        else:
            pass
        self.context.restore()

    def finish(self):
        '''Finishes the surface and writes it to the output file.'''

        # get the extension from the filename
        f, ext = os.path.splitext(self.targetfilename)
        # if this is a vector file, wrap up and finish
        if ext in (".svg",".ps",".pdf"):
            self.context.show_page()
            self.surface.finish()
        # but bitmap surfaces need us to tell them to save to a file
        elif ext == ".png":
            # write to file
            self.surface.write_to_png(self.targetfilename)
        else:
            raise ShoebotError(_("finish(): '%s' is an invalid extension") % ext)

    def run(self, inputcode=None):
        '''
        Executes the contents of a Nodebox/Shoebot script
        in current surface's context.
        '''

        source_or_code = ""

        if not inputcode:
        # no input? see if box has an input file name or string set
            if not self.inputscript:
                raise ShoebotError(_("run() needs an input file name or code string (if none was specified when creating the Box instance)"))
            inputcode = self.inputscript
        else:
            self.inputscript = inputcode

        # is it a proper filename?
        if os.path.exists(inputcode):
            filename = inputcode
            file = open(filename, 'rU')
            source_or_code = file.read()
            file.close()
        else:
            # if not, try parsing it as a code string
            source_or_code = inputcode

        import data
        for name in dir(self):
            # get all stuff in the Box namespaces
            self.namespace[name] = getattr(self, name)
        for name in dir(data):
            self.namespace[name] = getattr(data, name)

        try:
            # if it's a string, it needs compiling first; if it's a file, no action needed
            if isinstance(source_or_code, basestring):
                source_or_code = compile(source_or_code + "\n\n", "shoebot_code", "exec")
            # do the magic
            exec source_or_code in self.namespace
        except NameError:
            # if something goes wrong, print verbose system output
            # maybe this is too verbose, but okay for now
            errmsg = traceback.format_exc(limit=1)

#            print "Exception in Shoebot code:"
#            traceback.print_exc(file=sys.stdout)
            if not self.gtkmode:
                sys.stderr.write(errmsg)
                sys.exit()
            else:
                # if on gtkmode, print the error and don't break
                raise ShoebotError(errmsg)

#    def setup(self):
#        if self.namespace.has_key("setup"):
#            self.namespace["setup"]()
#        else:
#            raise ShoebotError("setup: There's no setup() method in input script")
#
#    def draw(self):
#        if self.namespace.has_key("draw"):
#            self.namespace["draw"]()
#        else:
#            raise ShoebotError("draw: There's no draw() method in input script")
#

class OptionsContainer:
    '''Used with the old Bot class.'''
    def __init__(self):
        #self.outputmode = RGB
        self.color_mode = RGB
        self.color_range = 1.

        self.fillapply = True
        self.strokeapply = False
        self.fillcolor = Color('#DDDDDD')
        self.strokecolor = Color('#222222')
        self.strokewidth = 1.0

        self.rectmode = 'corner'

        ## self.linecap
        ## self.linejoin
        ## self.fontweight
        ## self.fontslant
        ## self.hintmetrics
        ## self.hintstyle
        ## self.filter
        ## self.operator
        ## self.antialias
        ## self.fillrule

