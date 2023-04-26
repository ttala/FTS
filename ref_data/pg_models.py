from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, ForeignKey


Base = declarative_base()

class Airport(Base):
    __tablename__ = 'airport'
    __table_args__ = {"schema": "public"}
    iata = Column(String, primary_key=True)
    name = Column(String)
    city = Column(String)
    country = Column(String)
    #country_iata = Column(String, ForeignKey('public.country.country_iata'),nullable=False)
    #country = relationship('Country', back_populates='airline')
    
    def __repr__(self):
        return "<Airport(iata='{}', name='{}', cityt={}, country={})>"\
                .format(self.iata, self.name, self.city, self.country)


class Airline(Base):
    __tablename__ = 'airline'
    __table_args__ = {"schema": "public"}
    iata = Column(String, primary_key=True)
    name = Column(String)
    city = Column(String)
    country = Column(String)
    #country_iata = Column(String, ForeignKey('public.country.country_iata'),nullable=False)
    #country = relationship('Country', back_populates='airline')
    
    def __repr__(self):
        return "<Airport(iata='{}', name='{}', cityt={}, country={})>"\
                .format(self.iata, self.name, self.city, self.country)

