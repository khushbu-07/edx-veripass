


# edx-veripass
Veripass - Identity verification tool

## Overview
This is the student verification subsystem. This Python library provides the face and ID verificarion implementation used by Open edX.

## Dev Installation
To install edx-veripass:

``$ make lms-shell``

`` $ source /edx/app/edxapp/edxapp_env ``

`` $ pip install -e git+https://github.com/khushbu-07/edx-veripass.git@master#egg=edx-veripass ``



## Configuration
1. You will need to add new flag **ENABLE_VERIPASS** in lms.env.json and cms.env.json FEATURES dictionary:
```sh
"FEATURES": {
    :
    "ENABLE_VERIPASS": true,
    :
}
```

2. Add url in urls.py above **plugin_urls**
``` sh
if settings.FEATURES.get('ENABLE_VERIPASS', False):
    urlpatterns += [  
        url(r'', include('edx_veripass.urls', namespace='edx_veripass')),  
  	] 
```
 
3. Add link in header after `SysAdmin` 

File: edx-platform/lms/templates/header/navbar-authenticated.html


```sh
% if settings.FEATURES.get('ENABLE_VERIPASS', False) and not (user.is_staff or user.is_superuser or user.courseaccessrole_set.count()):  
    <div class="mobile-nav-item hidden-mobile nav-item nav-tab">  
	    ## Translators: This is short for "Veripass".  
        <a class="tab-nav-link" href="${reverse('edx_veripass:veripass')}">${_("Veripass")}</a>  
    </div>  
% endif
```

4. You will need to restart services after these configuration changes for them to take effect.
This verification tool is for students only.

5. After restarting the service and login with student account, students can see  **Veripass**  link at header and can see verification too as shown below.

 ![veripass dashboard](docs/images/edx-veripass.png) 

<!-- <img src="edx-veripass.png"
     alt="Markdown Monster icon"
     style="float: left; margin-right: 10px; width: 500px; height: 300px;" /> -->

## Getting Help
Have a question about this repository, or about Open edX in general? Please refer to this [list of resources](https://open.edx.org/community/connect) if you need any assistance.