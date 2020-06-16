import 'dart:core';
import 'package:cloud_firestore/cloud_firestore.dart';
import 'package:flutter/cupertino.dart';
import 'package:flutter/material.dart';
import 'package:personalapp/complete.dart';
import 'package:personalapp/main.dart';

void main() {
  runApp(complete());
}

class complete extends StatelessWidget {
  // This widget is the root of your application.
  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      routes: {
        'pend':(context) => MyApp(),
        'comp':(context) => complete(),
      },
      theme: ThemeData(
        brightness: Brightness.dark,
        primarySwatch: Colors.yellow,
        visualDensity: VisualDensity.adaptivePlatformDensity,
      ),
      home: MyHomePage(),
    );
  }
}

class MyHomePage extends StatefulWidget {

  @override
  _MyHomePageState createState() => _MyHomePageState();
}
class _MyHomePageState extends State<MyHomePage> {
  int _currentIndex = 1;
  final database = Firestore.instance;
  final GlobalKey<NavigatorState> navigatorKey = new GlobalKey<NavigatorState>();
  final GlobalKey<ScaffoldState> _scaffold = new GlobalKey<ScaffoldState>();
  void onTabTapped(int index) {
    switch(index){
      case 0:
        navigatorKey.currentState.pushReplacementNamed("pend");
        break;
      case 1:
        navigatorKey.currentState.pushReplacementNamed("comp");
    }
  }
  Widget _card(bool comp,DocumentSnapshot doc){
    if(comp){
      return new Card(
        shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(20.0)
        ),
        color: Colors.green,
        child: Padding(
          padding: const EdgeInsets.all(16.0),
          child: Row(mainAxisSize: MainAxisSize.max,
              children: [
                Expanded(child: Text(doc['task'].toString(),style: TextStyle(fontSize: 20,),)),
                Icon(Icons.check,size: 25,color: Colors.white,)
              ]),
        ),
      );
    }
    else
      return Container();
  }

  @override
  Widget build(BuildContext context) {
    return SafeArea(
      child: Scaffold(
        floatingActionButtonLocation: FloatingActionButtonLocation.centerFloat,
        key: _scaffold,
        floatingActionButton: FloatingActionButton(backgroundColor: Colors.orange,child: Icon(Icons.add),onPressed: (){},),
        appBar: AppBar(backgroundColor: Colors.blueAccent,
          title: Text("TODO",style: TextStyle(fontSize: 25,fontWeight: FontWeight.bold),),
          centerTitle: true,),
        body: StreamBuilder<QuerySnapshot>(
          stream: database.collection("todo").getDocuments().asStream(),
          builder: (BuildContext context, AsyncSnapshot<QuerySnapshot> snapshot){
            if(snapshot.hasError)
              return Text("Error: ${snapshot.error}");
            switch (snapshot.connectionState){
              case ConnectionState.waiting : return Center(child: new CircularProgressIndicator(backgroundColor: Colors.white,));
              default:
                return new ListView(
                  children: snapshot.data.documents.map((DocumentSnapshot doc){
                    return Padding(
                      padding: const EdgeInsets.all(8.0),
                      child: _card(doc["completed"], doc),
                    );
                  }).toList(),
                );
            }
          },
        ),
        bottomNavigationBar: BottomNavigationBar(
          onTap: onTabTapped,
          currentIndex: _currentIndex,
          backgroundColor: Colors.orangeAccent,
          items:[
            BottomNavigationBarItem(
              icon: Icon(Icons.access_time,size: 20,),
              title: Text("Pending",style: TextStyle(color: Colors.white),),
              activeIcon: Icon(Icons.access_time, size: 30,color: Colors.white,),
            ),

            BottomNavigationBarItem(
                icon: Icon(Icons.check,size: 20,),
                activeIcon: Icon(Icons.check,size: 30,),
                title: Text("Completed" , style: TextStyle(color: Colors.white),)
            ),
          ],
        ),
      ),
    );
  }
}
