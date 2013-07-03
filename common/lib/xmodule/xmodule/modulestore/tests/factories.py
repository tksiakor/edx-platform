from factory import Factory
from uuid import uuid4
from xmodule.modulestore import Location
from xmodule.modulestore.django import modulestore
import factory
from xmodule.course_module import CourseDescriptor
from xblock.core import Scope


class XModuleCourseFactory(Factory):
    """
    Factory for XModule courses.
    """

    ABSTRACT_FACTORY = True

    @classmethod
    def _create(cls, target_class, **kwargs):

        org = kwargs.pop('org', None)
        number = kwargs.pop('number', kwargs.pop('course', None))
        display_name = kwargs.pop('display_name', None)
        location = Location('i4x', org, number, 'course', Location.clean(display_name))

        try:
            store = modulestore('direct')
        except KeyError:
            store = modulestore()

        # Write the data to the mongo datastore
        if display_name is None:
            metadata = {}
        else:
            metadata = {'display_name': display_name}

        # NOTE: these factories in general aren't really valid tests as this hardcoding shows.
        metadata['tabs'] = kwargs.pop('tabs',
            [{"type": "courseware"},
                {"type": "course_info", "name": "Course Info"},
                {"type": "discussion", "name": "Discussion"},
                {"type": "wiki", "name": "Wiki"},
                {"type": "progress", "name": "Progress"}
            ]
        )

        data = kwargs.pop('data', {})

        # The rest of kwargs become attributes on the course:
        for k, v in kwargs.iteritems():
            field = getattr(CourseDescriptor, k)
            if field.scope == Scope.settings:
                metadata[k] = v
            elif field.scope == Scope.content:
                data[k] = v
            else:
                raise Exception("Don't know where to put {}".format(k))

        store.create_and_save_xmodule(location, metadata=metadata, definition_data=data)
        new_course = store.get_item(location)

        # clone a default 'about' module as well
        dest_about_location = location._replace(category='about', name='overview')
        store.create_and_save_xmodule(dest_about_location, system=new_course.system)

        return new_course


class Course:
    pass


class CourseFactory(XModuleCourseFactory):
    FACTORY_FOR = Course

    org = 'MITx'
    number = '999'
    display_name = 'Robot Super Course'


class XModuleItemFactory(Factory):
    """
    Factory for XModule items.
    """

    ABSTRACT_FACTORY = True

    parent_location = 'i4x://MITx/999/course/Robot_Super_Course'
    category = 'problem'
    display_name = factory.LazyAttributeSequence(lambda o, n: "{} {}".format(o.category, n))

    @staticmethod
    def location(parent, category, display_name):
        dest_name = display_name.replace(" ", "_") if display_name is not None else uuid4().hex
        return Location(parent).replace(category=category, name=dest_name)

    @classmethod
    def _create(cls, target_class, **kwargs):
        """
        Uses *kwargs*:

        *parent_location* (required): the location of the parent module
            (e.g. the parent course or section)

        category: the category of the resulting item.

        *data* (optional): the data for the item
            (e.g. XML problem definition for a problem item)

        *display_name* (optional): the display name of the item

        *metadata* (optional): dictionary of metadata attributes

        *target_class* is ignored
        """

        DETACHED_CATEGORIES = ['about', 'static_tab', 'course_info']
        # catch any old style users before they get into trouble
        assert not 'template' in kwargs
        parent_location = Location(kwargs.get('parent_location'))
        data = kwargs.get('data')
        category = kwargs.get('category')
        display_name = kwargs.get('display_name')
        metadata = kwargs.get('metadata', {})
        location = kwargs.get('location', XModuleItemFactory.location(parent_location, category, display_name))
        assert location != parent_location

        store = modulestore('direct')

        # This code was based off that in cms/djangoapps/contentstore/views.py
        parent = store.get_item(parent_location)

        # replace the display name with an optional parameter passed in from the caller
        if display_name is not None:
            metadata['display_name'] = display_name
        # note that location comes from above lazy_attribute
        store.create_and_save_xmodule(location, metadata=metadata, definition_data=data)

        if location.category not in DETACHED_CATEGORIES:
            parent.children.append(location.url())
            store.update_children(parent_location, parent.children)

        return store.get_item(location)


class Item:
    pass


class ItemFactory(XModuleItemFactory):
    FACTORY_FOR = Item
    category = 'chapter'
