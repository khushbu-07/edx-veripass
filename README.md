
# edx-veripass
This is the student verification subsystem that used in exam proctoring subsystem for the Open edX platform.

## Dev Installation
To install edx-veripass:

``$ make lms-shell``

`` $ source /edx/app/edxapp/edxapp_env ``

`` $ pip install git+https://github.com/khushbu-07/edx-veripass.git@master ``



## Configuration
1. You will need to add new flag `ENABLE_VERIPASS` in lms.env.json and cms.env.json FEATURES dictionary:

2. Add flag in lms > envs > production.py.
	`` ENABLE_VERIPASS = ENV_TOKENS.get('ENABLE_VERIPASS', False) ``

3. Add url in urls.py above **plugin_urls**
``` sh
if settings.FEATURES.get('ENABLE_VERIPASS', False):
    urlpatterns += [  
        url(r'', include('edx_veripass.urls', namespace='edx_veripass')),  
  	] 
```
 
4. Add link in header after `SysAdmin` 

File: edx-platform/lms/templates/header/navbar-authenticated.html


```sh
% if settings.FEATURES.get('ENABLE_VERIPASS', False) and not (user.is_staff or user.is_superuser or user.courseaccessrole_set.count()):  
    <div class="mobile-nav-item hidden-mobile nav-item nav-tab">  
	    ## Translators: This is short for "Veripass".  
        <a class="tab-nav-link" href="${reverse('edx_veripass:veripass')}">${_("Veripass")}</a>  
    </div>  
% endif
```