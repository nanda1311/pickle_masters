from django.contrib import admin
from django.urls import path
from .views import *


urlpatterns = [
    #frontend
    path('home/', home, name="home"),

    path('', home, name='home'),
    path('about-us/',aboutus, name='aboutus'),
    path('contact-us/', contactus, name='contactus'),
    path('login/', login_page, name='login'),
    path('sign-up/', signin, name='signin'),
    path('logout/', logout_user, name='logout'),
    path('privacy-policy/', privacy_policy, name='privacy_policy'),
    path('product/<slug:slug>/', product_detail, name='product_detail'),
    path('profile/', profile_page, name='profile'),
    path('profile/address/', address_profile, name='address_profile'),


    path('addresses/create/', create_address, name='create_address'),
    path('addresses/create/', create_address, name='create_address'),
    path('addresses/get/<int:pk>/', get_address, name='get_address'),
    path('addresses/update/<int:pk>/', update_address, name='update_address'),
    path('addresses/delete/<int:pk>/', delete_address, name='delete_address'),
    path('addresses/set-default/<int:pk>/', set_default_address, name='set_default_address'),


    path('profile/orders/', orders_page, name='orders_page'),
    path('profile/update-profile/', update_profile, name='update_profile'),
    path('shop/', shop, name='shop'),
    path('categories/<slug:slug>/', cateogry_products, name="cateogry_products"),
    path('terms-and-conditions/', terms_and_conditions, name='terms_and_conditions'),
    path('shipping_policy/', shipping_policy, name='shipping_policy'),
    path('returnandrefund_policy/', returnandrefund_policy, name='returnandrefund_policy'),
    path('Cancellation_policy/', cancellation_policy, name='cancellation_policy'),
    path('product/category/<slug:slug>/', cateogry_products, name='cateogry_products'),
    path('category/', category_list_view, name='category_list'),
    path('add-to-cart/', add_to_cart, name='add_to_cart'),

    path('cart/', cart_view, name='cart'),
    path('add-to-cart-ajax/', add_to_cart_ajax, name='add_to_cart_ajax'), # <--- ADD THIS
    path('cart/update/<int:cart_id>/', update_cart_quantity, name='update_cart_quantity'),
    path('cart/delete/<int:cart_id>/', delete_cart_item, name='delete_cart_item'),

    path('checkout/', checkout_from_cart, name='checkout'),


 
    # path('api/addresses/', AddressListCreateView.as_view(), name='address-list-create'),
    # path('api/addresses/<slug:slug>/', AddressDetailView.as_view(), name='address-detail'),


    #backend 
    path('account/login/', adminlogin_page, name='adminlogin'),
    path('account/logout/', adminlogout_page, name='adminlogout'),
    path('account/', dashboard, name='dashboard'),
    # category
    path('account/categories/', categories, name="categories"),
    path('account/category/<slug:slug>/edit/', categories, name='edit_category'),
    path('account/category/<slug:slug>/delete/', categories, name='delete_category'),


    # product
    path('account/products/', products, name='products'),
    path('account/create/product/', create_product, name='create_product'),
    path('account/update/product/<slug:slug>/', edit_product, name='edit_product'),
    path('account/delete/product/<slug:slug>/', delete_product, name='delete_product'),
    path('account/products/image/<int:image_id>/delete/', delete_product_image, name='delete_product_image'),




    path('account/order/checkout/', order_checkout, name='order_checkout'),
    path('account/order/detail/<int:pk>/', order_detail, name='order_detail'),
    path('account/order/collect-cash/<int:order_id>/', collect_cash, name='collect_cash'),
    path('account/orders/list/', orders_list, name='orders_list'),
    path('account/product/details/', product_details, name='product_details'),
    path('account/payments/list/', payment_list, name='payment_list'),
    path('account/purchase/order/', purchase_order, name='purchase_order'),
    path('account/purchase/returns/', purchase_returns, name='purchase_returns'),
    path('account/settings/', settings, name='settings'),
]

